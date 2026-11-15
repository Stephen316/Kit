import argparse
import errno
import os
import secrets
import shutil
import signal
import sys
import time
from pathlib import Path

from Adapters import load_adapter
from Processes import KILL_SIGNAL, process_start, signal_group, stop_orphan
from Records import bounded, canonical, label, read_record, reason_text
from ResourceBudget import ResourceBudget
from Runners import Registry
from Sessions import Session, read_bounded, write_private

CONFIG_KEYS = {"state", "controller", "registry", "worker", "pools", "resources", "stop_grace_seconds", "poll_seconds", "max_log_bytes", "reserved_cpus", "reserved_memory_mib", "adaptive_limits"}
ROOT = Path(__file__).resolve().parents[2]


class Busy(Exception):
    pass


def read_config(path):
    if sys.platform == "win32" and (sys.version_info < (3, 14) or sys.getwindowsversion().major < 10):
        raise ValueError("Windows supervision requires Windows 10 or newer and Python 3.14 or newer")
    path = Path(path).resolve()
    config = read_record(path)
    if not {"state", "controller", "registry", "pools"} <= config.keys() or config.keys() - CONFIG_KEYS:
        raise ValueError("supervisor configuration fields do not match version 1")
    if not isinstance(config["pools"], dict) or not 1 <= len(config["pools"]) <= 64:
        raise ValueError("pools must configure 1–64 pools")
    pools = {}
    for name, settings in config["pools"].items():
        if not isinstance(settings, dict) or set(settings) != {"max_sessions"}:
            raise ValueError(f"pool {name} must set only max_sessions")
        pools[label(name)] = {"max_sessions": bounded(settings["max_sessions"], 1, 64)}
    resources = config.get("resources", {})
    if not isinstance(resources, dict) or len(resources) > 64:
        raise ValueError("resources must map at most 64 names to capacities")
    grace = config.get("stop_grace_seconds", 10)
    poll = config.get("poll_seconds", 0.2)
    if type(grace) not in (int, float) or not 0.1 <= grace <= 60:
        raise ValueError("stop_grace_seconds must be between 0.1 and 60")
    if type(poll) not in (int, float) or not 0.05 <= poll <= 5:
        raise ValueError("poll_seconds must be between 0.05 and 5")
    adaptive = config.get("adaptive_limits", True)
    if type(adaptive) is not bool:
        raise ValueError("adaptive_limits must be a boolean")
    for key in ("state", "registry"):
        if not isinstance(config[key], str) or not config[key]:
            raise ValueError(f"{key} must be a path")
    resolve = lambda value: (Path(value) if Path(value).is_absolute() else path.parent / value).resolve()
    if not isinstance(config["controller"], dict):
        raise ValueError("controller configuration must be an object")
    controller = dict(config["controller"])
    for key in ("store", "module"):
        if isinstance(controller.get(key), str) and controller[key]:
            controller[key] = str(resolve(controller[key]))
    return {
        "state": resolve(config["state"]), "registry": resolve(config["registry"]), "controller": controller,
        "worker": label(config.get("worker", "supervisor:local")), "pools": pools,
        "resources": {label(name): bounded(capacity, 1, 64) for name, capacity in resources.items()},
        "grace": float(grace), "poll": float(poll),
        "max_log_bytes": bounded(config.get("max_log_bytes", 1048576), 1024, 67108864),
        "reserved_cpus": bounded(config.get("reserved_cpus", 2), 0, 65536),
        "reserved_memory_mib": bounded(config.get("reserved_memory_mib", 4096), 0, 1048576),
        "adaptive_limits": adaptive,
    }


def lock(path):
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        os.close(descriptor)
        if isinstance(error, BlockingIOError) or (sys.platform == "win32" and error.errno in (errno.EACCES, errno.EDEADLK)):
            raise Busy(f"another supervisor holds {path}") from None
        raise
    return descriptor


class Supervisor:
    def __init__(self, config, claiming):
        self.config = config
        self.root = ROOT
        self.state = config["state"]
        self.sessions = self.state / "sessions"
        self.claims = self.state / "claims"
        self.grace = config["grace"]
        self.max_log_bytes = config["max_log_bytes"]
        self.adapter = load_adapter(config["controller"], ROOT)
        self.registry = Registry(config["registry"], ROOT) if claiming else None
        self.budget = ResourceBudget(config, self.registry) if claiming else None
        self.admission = {}
        self.measurement_error = None
        self.running = {}
        self.locks = []
        self.counts = {"started": 0, "stale": 0, "orphans": 0, "finished": {}}
        self.stopping = False

    def acquire(self):
        for directory in (self.state, self.sessions, self.claims):
            directory.mkdir(mode=0o700, parents=directory is self.state, exist_ok=True)
        self.locks.append(lock(self.state / "supervisor.lock"))
        adapter_lock = self.adapter.LockPath()
        if adapter_lock is not None:
            Path(adapter_lock).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.locks.append(lock(adapter_lock))

    def report(self, action, session, detail):
        record = {"event": action, "at": time.time(), **detail}
        if session is not None:
            record.update({"session": session.name, "pool": session.pool, "job": session.spec["id"], "attempt": session.claim["attempt"]})
        print(canonical(record), flush=True)

    def pauses(self):
        path = self.state / "pauses.json"
        if not path.is_file():
            return {}
        record = read_bounded(path)
        return record.get("pools", {}) if isinstance(record, dict) else {}

    def recover(self):
        known = set()
        for directory in sorted(self.sessions.iterdir()):
            known.add(directory.name)
            claim_path = self.claims / f"{directory.name}.json"
            record = {}
            try:
                record = read_bounded(directory / "session.json")
            except (OSError, ValueError, UnicodeDecodeError):
                pass
            pid = record.get("pid")
            recorded = record.get("process_start")
            matched = type(pid) is int and isinstance(recorded, str) and process_start(pid) == recorded
            stopped = stop_orphan(pid, recorded, self.grace, record.get("job_object")) if matched else False
            if matched and not stopped:
                raise OSError(f"session process group could not be stopped: {directory.name}")
            receipt = {
                "receipt_version": 1, "session": directory.name, "job_id": record.get("job_id"), "attempt": record.get("attempt"),
                "pid": pid, "process_start": recorded, "identity_matched": matched, "stopped": stopped,
                "stop_reason": "supervisor_restart", "orphan": True, "recovered_at": time.time(),
            }
            write_private(directory / "receipt.json", receipt)
            self.counts["orphans"] += 1
            self.release(directory.name, claim_path, receipt, "orphaned by supervisor restart")
            shutil.rmtree(directory, ignore_errors=True)
        for claim_path in sorted(self.claims.glob("*.json")):
            if claim_path.stem not in known:
                self.release(claim_path.stem, claim_path, {"receipt_version": 1, "session": claim_path.stem, "orphan": True, "stop_reason": "claimed_before_start"}, "claimed before session start")

    def release(self, name, claim_path, receipt, reason):
        stale = None
        if claim_path.is_file():
            payload = self.state / f".release-{name}.json"
            write_private(payload, {"session_version": 1, "receipt": receipt, "result": None, "error": None, "stderr_tail": None})
            try:
                stale = self.adapter.FinishJob(claim_path, "retry", payload, reason)["stale"]
            finally:
                payload.unlink(missing_ok=True)
            claim_path.unlink(missing_ok=True)
        print(canonical({"event": "orphan", "at": time.time(), "session": name, "stale": stale, **{key: receipt.get(key) for key in ("job_id", "pid", "identity_matched", "stopped")}}), flush=True)

    def synchronize(self):
        pools = self.registry.pools()
        unknown = sorted(set(pools) - set(self.config["pools"]))
        unused = sorted(set(self.config["pools"]) - set(pools))
        if unknown or unused:
            raise ValueError(f"registry and configuration pools differ: {', '.join(unknown + unused)}")
        for name, kinds in sorted(pools.items()):
            self.adapter.DefinePool(name, kinds)
        for name, capacity in sorted(self.config["resources"].items()):
            self.adapter.DefineResource(name, capacity)

    def settle(self, session, outcome, reason, payload):
        reason = reason_text(reason)
        stale = None
        if session.stop_reason == "stale_lease":
            self.counts["stale"] += 1
        else:
            path = session.directory / "finish.json"
            write_private(path, payload)
            stale = self.adapter.FinishJob(session.claim_path, outcome, path, reason)["stale"]
            self.budget.record(session.spec, session.name, outcome, stale, payload["receipt"], self.report)
            finished = self.counts["finished"]
            finished[outcome] = finished.get(outcome, 0) + 1
        self.report("finished", session, {"outcome": None if session.stop_reason == "stale_lease" else outcome, "reason": reason, "stale": stale, "receipt": payload["receipt"]})
        session.remove()
        return True

    def fill(self, paused):
        claimed = False
        for pool, settings in sorted(self.config["pools"].items()):
            if pool in paused:
                continue
            while sum(1 for session in self.running.values() if session.pool == pool) < settings["max_sessions"]:
                admission = self.budget.admission(pool, settings, self.running)
                previous = self.admission.get(pool)
                self.admission[pool] = admission
                if previous is None or previous["reason"] != admission["reason"] or previous["active_limit"] != admission["active_limit"] or previous["adaptive_revision"] != admission["adaptive_revision"] or previous["upward_blocked_reason"] != admission["upward_blocked_reason"]:
                    self.report("admission", None, {"pool": pool, **admission})
                if admission["additional_sessions"] == 0:
                    break
                name = f"{time.time_ns():x}-{secrets.token_hex(4)}"
                claim_path = self.claims / f"{name}.json"
                claim = self.adapter.ClaimJob(pool, self.config["worker"], claim_path)
                if claim is None:
                    break
                claimed = True
                session = None
                try:
                    if claim["job"]["kind"] not in self.registry.runners or self.registry.runners[claim["job"]["kind"]]["pool"] != pool:
                        raise ValueError("claimed job kind has no runner in this pool")
                    session = Session(self, pool, claim, claim_path, name)
                    session.prepare()
                    session.start()
                except (OSError, ValueError, KeyError, TypeError) as error:
                    if session is not None and session.process is not None:
                        signal_group(session.process.pid, KILL_SIGNAL)
                        session.process.wait()
                        for capture in session.logs.values():
                            capture.close()
                        if sys.platform == "win32":
                            session.process.close()
                    path = self.state / f".setup-{name}.json"
                    detail = f"session setup failed: {type(error).__name__}: {error}"[:2048]
                    write_private(path, {"session_version": 1, "receipt": None, "result": None, "error": detail, "stderr_tail": None})
                    try:
                        self.adapter.FinishJob(claim_path, "retry", path, detail)
                    finally:
                        path.unlink(missing_ok=True)
                        shutil.rmtree(self.sessions / name, ignore_errors=True)
                        claim_path.unlink(missing_ok=True)
                    self.report("setup_failed", None, {"session": name, "pool": pool, "job": claim.get("job", {}).get("id"), "error": detail})
                    continue
                self.running[name] = session
                self.budget.adaptive.started(pool)
                self.counts["started"] += 1
                self.report("started", session, {"pid": session.pid})
        return claimed

    def shutdown(self, number, frame):
        self.stopping = True

    def run(self, idle_seconds, max_seconds):
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        self.acquire()
        self.recover()
        self.synchronize()
        self.budget.refresh(self.running)
        started = time.monotonic()
        last_work = started
        while True:
            now = time.time()
            paused = self.pauses()
            try:
                self.budget.refresh(self.running)
            except (OSError, ValueError) as error:
                self.measurement_error = str(error)[:2048]
                self.report("resource_measurement_error", None, {"error": self.measurement_error})
                for session in self.running.values():
                    session.begin_stop("resource_measurement_unavailable", now)
                self.stopping = True
            for name, session in list(self.running.items()):
                if session.tend(now, paused):
                    del self.running[name]
            if self.stopping or (max_seconds is not None and time.monotonic() - started >= max_seconds):
                break
            if self.fill(paused) or self.running:
                last_work = time.monotonic()
            elif idle_seconds is not None and time.monotonic() - last_work >= idle_seconds:
                break
            time.sleep(self.config["poll"])
        for session in self.running.values():
            session.begin_stop("supervisor_shutdown", time.time())
        while self.running:
            now = time.time()
            for name, session in list(self.running.items()):
                if session.tend(now, {}):
                    del self.running[name]
            time.sleep(0.05)
        if self.measurement_error is not None:
            raise OSError(self.measurement_error)
        return {"summary": self.counts}


def status(config):
    sessions = config["state"] / "sessions"
    running = {}
    if sessions.is_dir():
        for directory in sessions.iterdir():
            try:
                record = read_bounded(directory / "session.json")
            except (OSError, ValueError, UnicodeDecodeError):
                continue
            running.setdefault(record.get("pool"), []).append({key: record.get(key) for key in ("session", "job_id", "attempt", "pid", "started_at")})
    path = config["state"] / "pauses.json"
    pauses = read_bounded(path).get("pools", {}) if path.is_file() else {}
    return {"pools": {name: {"max_sessions": settings["max_sessions"], "running": sorted(running.get(name, []), key=lambda item: item["session"]), "paused": pauses.get(name)} for name, settings in sorted(config["pools"].items())}}


def set_pause(config, pool, reason):
    if pool not in config["pools"]:
        raise ValueError("pool is not configured")
    config["state"].mkdir(mode=0o700, parents=True, exist_ok=True)
    path = config["state"] / "pauses.json"
    pauses = read_bounded(path).get("pools", {}) if path.is_file() else {}
    if reason is None:
        pauses.pop(pool, None)
    else:
        pauses[pool] = {"reason": reason_text(reason), "at": time.time()}
    write_private(path, {"pools": pauses})
    return {"pool": pool, "paused": pauses.get(pool)}


def main():
    parser = argparse.ArgumentParser(description="Local research session supervisor")
    parser.add_argument("--config", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    running = commands.add_parser("run")
    running.add_argument("--idle-seconds", type=float)
    running.add_argument("--max-seconds", type=float)
    commands.add_parser("status")
    pause = commands.add_parser("pause")
    pause.add_argument("pool")
    pause.add_argument("--reason", required=True)
    resume = commands.add_parser("resume")
    resume.add_argument("pool")
    submit = commands.add_parser("submit")
    submit.add_argument("file", type=Path)
    binding = commands.add_parser("bind")
    binding.add_argument("name")
    binding.add_argument("file", type=Path)
    jobs = commands.add_parser("jobs")
    jobs.add_argument("--job")
    jobs.add_argument("--after")
    args = parser.parse_args()
    try:
        config = read_config(args.config)
        if args.command == "run":
            response = Supervisor(config, True).run(args.idle_seconds, args.max_seconds)
        elif args.command == "status":
            response = status(config)
        elif args.command in ("pause", "resume"):
            response = set_pause(config, args.pool, args.reason if args.command == "pause" else None)
        else:
            adapter = Supervisor(config, False).adapter
            if args.command == "submit":
                response = adapter.SubmitJobs(args.file.resolve())
            elif args.command == "bind":
                response = adapter.BindInput(args.name, args.file.resolve())
            else:
                response = adapter.ReadStatus(args.job, args.after)
        print(canonical(response), flush=True)
        return 0
    except Busy as error:
        print(f"supervisor busy: {error}", file=sys.stderr)
        return 4
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"supervisor error: {type(error).__name__}: {error}"[:4096], file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
