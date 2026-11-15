import json
import os
import secrets
import shutil
import signal
import sys
import time
from pathlib import Path

from LogCapture import LogCapture
from OutputManifest import InvalidOutput
from Processes import KILL_SIGNAL, finish_process, process_start, signal_group, start_process, stderr_tail
from Records import canonical
from Runners import result_error, safe_name

ENVIRONMENT = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ")


def write_private(path, value):
    path = Path(path)
    staged = path.with_name(f".{path.name}.{secrets.token_hex(8)}")
    descriptor = os.open(staged, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        output.write(canonical(value) + "\n")
        output.flush()
        os.fsync(output.fileno())
    os.replace(staged, path)


def read_bounded(path, limit=1024 * 1024):
    with Path(path).open("rb") as source:
        content = source.read(limit + 1)
    if len(content) > limit:
        raise ValueError("file exceeds 1 MiB")
    return json.loads(content.decode("utf-8"))


class Session:
    def __init__(self, supervisor, pool, claim, claim_path, name):
        self.supervisor = supervisor
        self.pool = pool
        self.claim = claim
        self.claim_path = claim_path
        self.name = name
        self.spec = claim["job"]
        self.directory = supervisor.sessions / name
        self.process = None
        self.pid = None
        self.started = time.time()
        self.deadline = claim["deadline"]
        self.stop_at = self.deadline - min(supervisor.grace + 2, self.spec["timeout_seconds"] / 2)
        self.renew_every = self.spec["lease_seconds"] / 3
        self.next_renew = self.started + self.renew_every
        self.stop_reason = None
        self.kill_at = None
        self.killed = False
        self.logs = {}
        self.memory_peak = 0
        self.memory_limit = supervisor.registry.runners[self.spec["kind"]]["max_memory_mib"] * 1048576

    def prepare(self):
        self.directory.mkdir(mode=0o700)
        (self.directory / "inputs").mkdir(mode=0o700)
        (self.directory / "work").mkdir(mode=0o700)
        inputs = {}
        for role, item in self.claim["snapshot"]["inputs"].items():
            digest = safe_name(item["sha256"])
            target = self.directory / "inputs" / digest
            if not target.exists():
                self.supervisor.adapter.FetchInput(digest, target)
            inputs[role] = {"binding": item["binding"], "sha256": digest, "path": f"inputs/{digest}"}
        write_private(self.directory / "job.json", {
            "session_version": 1, "session": self.name, "pool": self.pool, "job": self.spec,
            "generation": self.claim["generation"], "attempt": self.claim["attempt"],
            "fingerprint": self.claim["fingerprint"], "inputs": inputs,
            "dependencies": self.claim["snapshot"].get("dependencies", {}),
            "stop_at": self.stop_at, "result": "result.json", "work": "work",
        })

    def start(self):
        argv = self.supervisor.registry.argv(self.spec["kind"], self.directory)
        work = str(self.directory / "work")
        environment = {name: os.environ[name] for name in ENVIRONMENT if name in os.environ}
        environment.update({"HOME": work, "TMPDIR": work, "KIT_SESSION": str(self.directory)})
        if sys.platform == "win32":
            environment.update({name: os.environ[name] for name in ("SystemRoot", "WINDIR", "PATHEXT") if name in os.environ})
            environment.update({"USERPROFILE": work, "TEMP": work, "TMP": work})
        try:
            for name in ("stdout", "stderr"):
                self.logs[name] = LogCapture(self.directory / f"{name}.log", self.supervisor.max_log_bytes)
            self.process = start_process(argv, self.supervisor.root, environment, self.logs["stdout"].writer, self.logs["stderr"].writer)
        finally:
            for capture in self.logs.values():
                if self.process is None:
                    capture.close()
                else:
                    capture.close_writer()
        self.pid = self.process.pid
        self.process_start = self.process.identity if os.name == "nt" else process_start(self.pid)
        write_private(self.directory / "session.json", {
            "session_version": 1, "session": self.name, "pool": self.pool, "job_id": self.spec["id"],
            "attempt": self.claim["attempt"], "pid": self.pid, "process_start": self.process_start,
            "claim_file": str(self.claim_path), "started_at": self.started,
            "job_object": getattr(self.process, "job_name", None),
        })

    def begin_stop(self, reason, now):
        if self.stop_reason is not None:
            return
        self.stop_reason = reason
        signal_group(self.pid, signal.SIGTERM)
        self.kill_at = now + max(0.1, min(self.supervisor.grace, self.deadline - now - 1))

    def tend(self, now, paused):
        for capture in self.logs.values():
            capture.drain()
        memory = self.supervisor.budget.groups.get(self.pid)
        if memory is not None:
            self.memory_peak = max(self.memory_peak, memory)
        finished = finish_process(self.process)
        if finished is not None:
            return self.complete(finished)
        if self.stop_reason is not None:
            if not self.killed and now >= self.kill_at:
                signal_group(self.pid, KILL_SIGNAL)
                self.killed = True
            return None
        if memory is None:
            self.begin_stop("resource_measurement_unavailable", now)
            return None
        if memory > self.memory_limit:
            self.begin_stop("memory_limit", now)
            return None
        if now >= self.next_renew:
            try:
                lease = self.supervisor.adapter.RenewLease(self.claim_path)
            except Exception as error:
                self.supervisor.report("renew_error", self, {"error": f"{type(error).__name__}: {error}"[:2048]})
                self.next_renew = now + min(1, self.renew_every)
            else:
                if lease["stale"]:
                    self.begin_stop("stale_lease", now)
                    return None
                self.next_renew = now + self.renew_every
        if now >= self.stop_at:
            self.begin_stop("deadline", now)
        elif self.pool in paused:
            self.begin_stop("pool_paused", now)
        return None

    def complete(self, exit_info):
        for capture in self.logs.values():
            capture.close()
        ended = time.time()
        signaled = exit_info["signal"] is not None
        receipt = {
            "receipt_version": 1, "session": self.name, "pool": self.pool, "job_id": self.spec["id"],
            "kind": self.spec["kind"], "attempt": self.claim["attempt"], "pid": self.pid,
            "process_start": self.process_start, "exit_status": exit_info["exit_status"],
            "signal": exit_info["signal"], "stop_reason": self.stop_reason,
            "started_at": self.started, "ended_at": ended, "duration_seconds": ended - self.started,
            "peak_memory_bytes": exit_info["peak_memory_bytes"], "orphan": False,
            "logs": {name: capture.receipt() for name, capture in self.logs.items()},
            "sampled_group_peak_memory_bytes": self.memory_peak,
            "memory_limit_bytes": self.memory_limit,
        }
        write_private(self.directory / "receipt.json", receipt)
        result, error, tail = None, None, None
        if self.stop_reason is not None:
            outcome, reason = "retry", f"session stopped: {self.stop_reason}"
        elif signaled:
            outcome, reason = "retry", f"runner ended by signal {receipt['signal']}"
        elif receipt["exit_status"] != 0:
            tail = stderr_tail(self.directory / "stderr.log")
            outcome, reason = "retry", f"runner exited with status {receipt['exit_status']}"
        else:
            try:
                result = read_bounded(self.directory / "result.json")
                error = result_error(result, self.supervisor.registry.runners[self.spec["kind"]]["schema"])
                if error is None and "artifacts" in result and getattr(self.supervisor.adapter, "OutputArtifactsVersion", None) != 1:
                    error = "controller adapter does not support version 1 output artifacts"
            except (OSError, ValueError, UnicodeDecodeError) as problem:
                result, error = None, f"{type(problem).__name__}: {problem}"[:2048]
            if error is None:
                outcome, reason = result["outcome"], result["reason"]
            else:
                outcome, reason, result = "retry", f"invalid result: {error}"[:2048], None
        try:
            return self.supervisor.settle(self, outcome, reason, {"session_version": 1, "receipt": receipt, "result": result, "error": error, "stderr_tail": tail})
        except InvalidOutput as problem:
            error = f"invalid output artifacts: {problem}"[:2048]
            return self.supervisor.settle(self, "retry", error, {"session_version": 1, "receipt": receipt, "result": None, "error": error, "stderr_tail": tail})

    def remove(self):
        if sys.platform == "win32" and self.process is not None:
            self.process.close()
        for capture in self.logs.values():
            capture.close()
        shutil.rmtree(self.directory, ignore_errors=True)
        Path(self.claim_path).unlink(missing_ok=True)
