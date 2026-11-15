import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from LinuxOomWitness import allocate_pages, check_worker_group, identity, require

CASES = ("ordinary_sigkill", "memory_cap")
JOB = "witness:linux-oom"
POOL = "decode"
PACKET_BYTES = 16384


def send(channel, message):
    content = json.dumps(message, separators=(",", ":")).encode("ascii")
    require(
        len(content) <= PACKET_BYTES and channel.send(content) == len(content),
        "incomplete observer message",
    )


def receive(channel, action):
    content, _, flags, _ = channel.recvmsg(PACKET_BYTES)
    require(
        content and not flags & socket.MSG_TRUNC,
        "missing or oversized observer message",
    )
    message = json.loads(content)
    require(
        isinstance(message, dict) and message.get("action") == action,
        f"unexpected observer message while awaiting {action}",
    )
    return message


class Observer:
    def __init__(self, channel):
        self.channel = channel

    def arm(self, session, pid, start):
        send(
            self.channel,
            {"action": "arm", "session": session, "pid": pid, "start": start},
        )
        receive(self.channel, "armed")
        return self

    def finish(self, receipt):
        keys = (
            "session",
            "pid",
            "process_start",
            "exit_status",
            "signal",
            "stop_reason",
            "orphan",
        )
        send(self.channel, {"action": "finish", **{key: receipt[key] for key in keys}})
        return receive(self.channel, "observation")["value"]

    def close(self):
        send(self.channel, {"action": "close"})
        receive(self.channel, "closed")


def write_record(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def prepare(repository, root, case, group):
    store = root / "Store"
    automation = repository / "re" / "automation"
    subprocess.run(
        [
            sys.executable,
            str(automation / "Controller.py"),
            "--store",
            str(store),
            "init",
        ],
        stdout=subprocess.DEVNULL,
        check=True,
        timeout=10,
    )
    schema = root / "Schema.json"
    registry = root / "Runners.json"
    config = root / "Supervisor.json"
    write_record(schema, {"type": "object"})
    write_record(
        registry,
        {
            "runners": {
                "witness.decode": {
                    "pool": POOL,
                    "result_schema": str(schema),
                    "threads": 1,
                    "initial_peak_memory_mib": 64,
                    "max_memory_mib": 256,
                    "argv": [
                        sys.executable,
                        "-I",
                        "-S",
                        str(Path(__file__).resolve()),
                        "worker",
                        case,
                        group,
                    ],
                }
            }
        },
    )
    write_record(
        config,
        {
            "state": str(root / "State"),
            "controller": {"adapter": "a03", "store": str(store)},
            "registry": str(registry),
            "pools": {POOL: {"max_sessions": 4}},
            "reserved_cpus": 0,
            "reserved_memory_mib": 4096,
            "adaptive_limits": True,
            "stop_grace_seconds": 1,
            "poll_seconds": 0.1,
        },
    )
    return automation, store, config


def stored_record(store, digest):
    require(
        isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest),
        "controller record lacks its digest",
    )
    content = (store / "objects" / digest[:2] / digest).read_bytes()
    require(
        hashlib.sha256(content).hexdigest() == digest, "controller record hash differs"
    )
    return json.loads(content)


def accepted_settlement(supervisor, store, events, session):
    finishes = [event for event in events if event.get("event") == "finished"]
    require(len(finishes) == 1, "expected one real supervisor settlement")
    finished = finishes[0]
    receipt = finished["receipt"]
    require(
        finished["stale"] is False
        and finished["outcome"] == "retry"
        and finished["job"] == receipt["job_id"] == JOB
        and session == receipt["session"],
        "supervisor did not accept the owned attempt",
    )
    (job,) = supervisor.adapter.ReadStatus(JOB, None)["jobs"]
    result = stored_record(store, job["result"])
    durable = stored_record(store, job["receipt"])
    require(
        job["id"] == JOB
        and job["state"] == "failed"
        and job["attempts"] == 1
        and durable["job_id"] == JOB
        and durable["outcome"] == "retry"
        and durable["attempt"] == 1
        and durable["generation"] == job["generation"]
        and durable["result_sha256"] == job["result"]
        and result["receipt"] == receipt,
        "durable controller settlement differs from the reported attempt",
    )
    return {
        "session": session,
        "job": JOB,
        "state": job["state"],
        "attempt": durable["attempt"],
        "generation": durable["generation"],
        "outcome": durable["outcome"],
        "stale": finished["stale"],
        "controller_receipt_sha256": job["receipt"],
        "result_sha256": job["result"],
        "pid": receipt["pid"],
        "process_start": receipt["process_start"],
        "signal": receipt["signal"],
        "stop_reason": receipt["stop_reason"],
        "kernel_oom": receipt.get("kernel_oom"),
    }


def supervise(descriptor, repository, root, case, group):
    require(os.geteuid() != 0 and os.getegid() != 0, "supervisor must be unprivileged")
    automation, store, config_file = prepare(repository, root, case, group)
    sys.path.insert(0, str(automation))
    from Supervisor import Supervisor, read_config

    config = read_config(config_file)
    batch = root / "Batch.json"
    write_record(
        batch,
        {
            "jobs": [
                {
                    "id": JOB,
                    "kind": "witness.decode",
                    "inputs": {},
                    "tool_version": "witness@1",
                    "rule_version": "witness@1",
                    "max_attempts": 1,
                    "lease_seconds": 20,
                    "timeout_seconds": 30,
                    "retry_base_seconds": 1,
                }
            ]
        },
    )
    Supervisor(config, False).adapter.SubmitJobs(batch)
    with socket.socket(fileno=descriptor) as channel:
        channel.settimeout(15)
        supervisor = Supervisor(config, True, linux_oom_observer=Observer(channel))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            summary = supervisor.run(1.0, 25)
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        require(
            summary["summary"]["started"] == 1, "expected one real supervisor launch"
        )
        starts = [event for event in events if event.get("event") == "started"]
        require(len(starts) == 1, "expected one start event")
        started = starts[0]
        admissions = [event for event in events if event.get("event") == "admission"]
        backoffs = [
            event for event in events if event.get("event") == "adaptive_backoff"
        ]
        keys = (
            "session",
            "job",
            "pool",
            "before_limit",
            "target_limit",
            "adaptive_reason",
            "adaptive_revision",
        )
        settlement = accepted_settlement(supervisor, store, events, started["session"])
        reloaded = Supervisor(config, True).budget.history
        kind, version = "witness.decode", "witness@1"
        initial = 64 * 1048576
        estimates = [
            {key: event[key] for key in (
                "session", "job", "group_size", "kind", "tool_version",
                "previous_estimate_bytes", "estimate_bytes", "samples", "source",
            )}
            for event in events if event.get("event") == "memory_estimate"
        ]
        persisted_estimate = reloaded.estimate(kind, version, initial)
        if settlement["kernel_oom"] is not None:
            original = reloaded.path.read_bytes()
            replayed = reloaded.record_oom(
                {"kind": kind, "tool_version": version}, settlement["session"], initial
            )
            require(
                replayed is None and reloaded.path.read_bytes() == original,
                "reloaded memory history applied an accepted OOM session twice",
            )
        send(
            channel,
            {
                "action": "result",
                "settlement": settlement,
                "started_pid": started["pid"],
                "group_size": started["group_size"],
                "initial_capacity": admissions[0]["calculated_capacity"],
                "initial_limit": admissions[0]["active_limit"],
                "final_limit": admissions[-1]["active_limit"],
                "backoffs": [{key: event[key] for key in keys} for event in backoffs],
                "initial_admission_estimate_bytes": admissions[0]["estimated_memory_bytes"],
                "final_admission_estimate_bytes": admissions[-1]["estimated_memory_bytes"],
                "memory_estimates": estimates,
                "reloaded_memory_estimate": persisted_estimate,
            },
        )


def worker(case, group):
    require(case in CASES, "unknown witness case")
    check_worker_group(group)
    session = Path(os.environ["KIT_SESSION"])
    record = json.loads((session / "session.json").read_text(encoding="utf-8"))
    own = identity(os.getpid())
    require(
        record["pid"] == own["pid"]
        and record["process_start"] == f"linux:{own['proc_start_ticks']}"
        and record["job_id"] == JOB
        and record["pool"] == POOL,
        "held worker did not see its own durable session record",
    )
    if case == "ordinary_sigkill":
        os.kill(os.getpid(), signal.SIGKILL)
    allocate_pages()
    return 72


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "worker":
        sys.exit(worker(*sys.argv[2:]))
    if len(sys.argv) == 7 and sys.argv[1] == "supervisor":
        supervise(int(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), *sys.argv[5:])
    else:
        raise SystemExit("expected a bounded supervisor or worker invocation")
