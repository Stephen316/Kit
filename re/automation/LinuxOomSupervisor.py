import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import subprocess
import sys
import tempfile
import time

STAGE = Path(__file__).resolve().parent
SOURCES = {"LinuxOomGuest.py", "LinuxOomSupervisor.py", "LinuxOomWitness.py"}


def source_identities(specifications):
    expected = {}
    for item in specifications:
        name, blob, digest = item.split(":")
        if (
            name not in SOURCES
            or name in expected
            or not re.fullmatch(r"[a-f0-9]{40}", blob)
            or not re.fullmatch(r"[a-f0-9]{64}", digest)
        ):
            raise ValueError("expected distinct pinned witness sources")
        expected[name] = {"git_blob": blob, "sha256": digest}
    if expected.keys() != SOURCES:
        raise ValueError("incomplete witness source set")
    return expected


def verify_sources(expected):
    if STAGE.stat().st_uid != 0 or STAGE.stat().st_mode & 0o022:
        raise ValueError("observer stage must be root owned and read only to its guest")
    for name, identities in expected.items():
        path = STAGE / name
        if path.is_symlink() or path.stat().st_uid != 0 or path.stat().st_mode & 0o022:
            raise ValueError(
                "observer sources must be root owned and read only to their guest"
            )
        source = path.read_bytes()
        header = f"blob {len(source)}\0".encode("ascii")
        if (
            hashlib.sha1(header + source, usedforsecurity=False).hexdigest()
            != identities["git_blob"]
            or hashlib.sha256(source).hexdigest() != identities["sha256"]
        ):
            raise ValueError("observer source identity differs")


def held_worker(pid, supervisor_pid, start, uid, repository, case, group):
    worker = witness.identity(pid)
    witness.require(
        worker["uid"] == uid and start == f"linux:{worker['proc_start_ticks']}",
        "worker identity differs from the held launch",
    )
    process = Path(f"/proc/{pid}")
    status = witness.read(process / "status")
    witness.require(
        re.search(rf"^PPid:\s+{supervisor_pid}$", status, re.MULTILINE)
        and int(witness.read(process / "oom_score_adj")) > -1000,
        "only an OOM-eligible direct child of the supervised guest can join the leaf",
    )
    argv = witness.read(process / "cmdline").rstrip("\0").split("\0")
    gate = repository / "re/automation/LaunchGate.py"
    guest = STAGE / "LinuxOomGuest.py"
    expected = [sys.executable, "-I", "-S", str(guest), "worker", case, group.name]
    witness.require(
        len(argv) == 12
        and argv[:4] == [sys.executable, "-I", "-S", str(gate)]
        and argv[4].isascii()
        and argv[4].isdecimal()
        and argv[5:] == expected,
        "held worker is outside the fixed launch command",
    )
    return worker


def observations(channel, pidfd, pid, worker, session, group, case, log):
    finish = guest.receive(channel, "finish")
    witness.require(
        finish
        == {
            "action": "finish",
            "session": session,
            "pid": pid,
            "process_start": f"linux:{worker['proc_start_ticks']}",
            "exit_status": None,
            "signal": signal.SIGKILL,
            "stop_reason": None,
            "orphan": False,
        },
        "supervisor wait receipt differs from the held worker",
    )
    witness.require(
        select.select([pidfd], [], [], 0)[0] and not Path(f"/proc/{pid}").exists(),
        "observer received a finish before the held process was reaped",
    )
    return {
        "case": case,
        "group": "/" + group.name,
        "worker": worker,
        "session": session,
        "termination": -signal.SIGKILL,
        "after": witness.observation(group, None),
        "kernel_messages": witness.kernel_hits(log, pid, group.name),
    }


def run_guest(channel, process, group, case, uid, repository, log):
    arm = guest.receive(channel, "arm")
    pid, start, session = (arm[key] for key in ("pid", "start", "session"))
    witness.require(
        type(pid) is int
        and pid > 1
        and isinstance(session, str)
        and re.fullmatch(r"[a-f0-9]+-[a-f0-9]{8}", session),
        "invalid held launch identity",
    )
    worker = held_worker(pid, process.pid, start, uid, repository, case, group)
    pidfd = os.pidfd_open(pid)
    try:
        witness.require(
            witness.identity(pid) == worker, "worker changed before containment"
        )
        (group / "cgroup.procs").write_text(f"{pid}\n", encoding="ascii")
        try:
            witness.require(
                witness.memberships(pid) == "/" + group.name
                and witness.identity(pid) == worker,
                "held worker changed during containment",
            )
            before = witness.observation(group, pid)
            witness.require(
                witness.read("/proc/sys/vm/panic_on_oom").strip() == "0",
                "panic_on_oom changed before worker release",
            )
            guest.send(channel, {"action": "armed"})
            observed = {
                **observations(channel, pidfd, pid, worker, session, group, case, log),
                "before": before,
            }
            guest.send(channel, {"action": "observation", "value": observed})
            guest.receive(channel, "close")
            guest.send(channel, {"action": "closed"})
            return observed, guest.receive(channel, "result")
        finally:
            with contextlib.suppress(ProcessLookupError):
                signal.pidfd_send_signal(pidfd, signal.SIGKILL)
            deadline = time.monotonic() + 3
            while (
                witness.read(group / "cgroup.procs").split()
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)
    finally:
        os.close(pidfd)


def verify_result(observed, result):
    settlement = result["settlement"]
    witness.require(
        set(result)
        == {
            "action",
            "settlement",
            "started_pid",
            "group_size",
            "initial_capacity",
            "initial_limit",
            "final_limit",
            "backoffs",
        }
        and set(settlement)
        == {
            "session",
            "job",
            "state",
            "attempt",
            "generation",
            "outcome",
            "stale",
            "controller_receipt_sha256",
            "result_sha256",
            "pid",
            "process_start",
            "signal",
            "stop_reason",
            "kernel_oom",
        }
        and all(
            isinstance(settlement[key], str)
            and re.fullmatch(r"[0-9a-f]{64}", settlement[key])
            for key in ("controller_receipt_sha256", "result_sha256")
        ),
        "unprivileged settlement fields do not match the sanitized report",
    )
    own = observed["worker"]
    group = observed["group"]
    before, after = observed["before"], observed["after"]
    original, final = before["memory_events_local"], after["memory_events_local"]
    witness.require(
        original.keys() == final.keys()
        and (before["device"], before["inode"]) == (after["device"], after["inode"]),
        "cgroup identity or counter schema changed",
    )
    delta = {key: final[key] - old for key, old in original.items()}
    witness.require(
        all(value >= 0 for value in delta.values())
        and result["group_size"] == 1
        and result["started_pid"] == settlement["pid"] == own["pid"]
        and settlement["session"] == observed["session"]
        and settlement["process_start"] == f"linux:{own['proc_start_ticks']}"
        and settlement["stale"] is False
        and settlement["attempt"] == 1
        and type(settlement["generation"]) is int
        and settlement["generation"] >= 0
        and settlement["outcome"] == "retry"
        and settlement["job"] == guest.JOB
        and settlement["state"] == "failed"
        and settlement["signal"] == signal.SIGKILL
        and settlement["stop_reason"] is None
        and result["initial_capacity"] == 4
        and result["initial_limit"] == 2,
        "current accepted settlement differs from the measured dispatch",
    )
    messages = observed["kernel_messages"]
    if observed["case"] == "memory_cap":
        witness.require(
            delta["max"] > 0
            and delta["oom"] > 0
            and delta["oom_kill"] == 1
            and delta.get("oom_group_kill", 0) == 0
            and len(messages) == 1
            and messages[0]["constraint"] == "CONSTRAINT_MEMCG"
            and messages[0]["uid"] == own["uid"]
            and messages[0]["oom_memcg"] == messages[0]["task_memcg"] == group,
            "kernel messages and local counters do not independently identify the victim",
        )
        witness.require(
            settlement["kernel_oom"]
            == {
                "evidence_version": 1,
                "kind": "linux_memcg_oom",
                "kernel_record": messages[0],
                "group": group,
                "device": before["device"],
                "inode": before["inode"],
                "local_delta": {key: delta[key] for key in ("max", "oom", "oom_kill")},
            },
            "durable OOM proof differs from privileged observation",
        )
        witness.require(
            result["final_limit"] == 1
            and result["backoffs"]
            == [
                {
                    "session": settlement["session"],
                    "job": guest.JOB,
                    "pool": guest.POOL,
                    "before_limit": 2,
                    "target_limit": 1,
                    "adaptive_reason": "linux_memcg_oom",
                    "adaptive_revision": 2,
                }
            ],
            "verified OOM did not reduce the adaptive target exactly once",
        )
    else:
        witness.require(
            not any(delta.values())
            and not messages
            and settlement["kernel_oom"] is None
            and result["final_limit"] == 2
            and not result["backoffs"],
            "ordinary SIGKILL changed counters or reduced the adaptive target",
        )
    return {
        **observed,
        "local_delta": delta,
        **{key: value for key, value in result.items() if key != "action"},
    }


def run_case(root, repository, case, uid, gid):
    case_root = root / case
    case_root.mkdir(mode=0o700)
    os.chown(case_root, uid, gid)
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    with parent, child, witness.private_group() as group, witness.kernel_log() as log:
        parent.settimeout(25)
        command = [
            sys.executable,
            "-I",
            "-S",
            str(STAGE / "LinuxOomGuest.py"),
            "supervisor",
            str(child.fileno()),
            str(repository),
            str(case_root),
            case,
            group.name,
        ]
        with subprocess.Popen(
            command,
            pass_fds=(child.fileno(),),
            cwd="/",
            env={},
            user=uid,
            group=gid,
            extra_groups=[],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            start_new_session=True,
        ) as process:
            child.close()
            try:
                observed, result = run_guest(
                    parent, process, group, case, uid, repository, log
                )
                witness.require(
                    process.wait(timeout=5) == 0,
                    "unprivileged supervisor did not exit cleanly",
                )
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
    witness.require(not group.exists(), "private worker cgroup was not removed")
    return verify_result(observed, result)


def publish(output, report, uid, gid):
    descriptor = os.open(
        output, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        os.fchown(file.fileno(), uid, gid)
        json.dump(report, file, indent=2, sort_keys=True)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())


def run(args):
    if (
        sys.platform != "linux"
        or os.geteuid() != 0
        or not re.fullmatch(r"[a-f0-9]{40}", args.revision)
    ):
        raise ValueError(
            "observer requires disposable Linux sudo and the exact checkout revision"
        )
    uid, gid = int(os.environ["SUDO_UID"]), int(os.environ["SUDO_GID"])
    if uid <= 0 or gid <= 0:
        raise ValueError("sudo caller must be unprivileged")
    expected = source_identities(args.source)
    verify_sources(expected)
    sys.path.insert(0, str(STAGE))
    import LinuxOomGuest
    import LinuxOomWitness

    global guest, witness
    guest, witness = LinuxOomGuest, LinuxOomWitness
    boot = witness.read("/proc/sys/kernel/random/boot_id")
    try:
        witness.preflight()
        if (
            len(os.sched_getaffinity(0)) < 4
            or witness.available_memory() < (4096 + 4 * 64) * 1048576
        ):
            raise witness.UnsupportedHost("host_cannot_admit_four_fixed_worker_slots")
    except witness.UnsupportedHost as error:
        result = {"status": "unmeasured", "reason": str(error)}
    else:
        with tempfile.TemporaryDirectory(
            prefix="kit-supervisor-oom-cases-", dir="/tmp"
        ) as directory:
            root = Path(directory)
            root.chmod(0o711)
            observations = [
                run_case(root, args.repository, case, uid, gid) for case in guest.CASES
            ]
        result = {"status": "observed", "cases": observations, "cleanup_verified": True}
    verify_sources(expected)
    witness.require(
        boot == witness.read("/proc/sys/kernel/random/boot_id"),
        "kernel boot identity changed",
    )
    publish(
        args.output,
        {
            "evidence_version": 1,
            "kernel": os.uname().release,
            "boot_id": boot.strip(),
            "source_revision": args.revision,
            "observer_sources": expected,
            "requested_limits": witness.LIMITS,
            "maximum_allocation_blocks": witness.MAX_BLOCKS,
            **result,
        },
        uid,
        gid,
    )
    print(result["status"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Witness bounded kernel OOM with real supervisor settlement"
    )
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--source", action="append", required=True)
    run(parser.parse_args())
