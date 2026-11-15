import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import stat
import subprocess
import sys


ROOT = Path("/sys/fs/cgroup")
CAP_BYTES = 64 * 1048576
MAX_BLOCKS = 96
GROUP_NAME = re.compile(r"kit-a08b-oom-[0-9a-f]{16}")
LIMITS = {
    "memory.max": str(CAP_BYTES),
    "memory.swap.max": "0",
    "memory.oom.group": "0",
    "pids.max": "1",
    "cgroup.max.descendants": "0",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path, limit=8192):
    with Path(path).open("rb") as file:
        content = file.read(limit + 1)
    require(len(content) <= limit, f"oversized kernel record: {path}")
    return content.decode("ascii")


def check_limits(group):
    expected = {**LIMITS, "cgroup.type": "domain"}
    for field, value in expected.items():
        require(read(group / field).strip() == value, f"unexpected private group control: {field}")


def available_memory():
    content = read("/proc/meminfo")
    match = re.search(r"^MemAvailable:\s+([0-9]+) kB$", content, re.MULTILINE)
    require(match is not None, "no host MemAvailable counter")
    available = int(match[1]) * 1024
    require(available >= 4 * 1024**3, "host has less than 4 GiB available")
    return available


def memberships(pid):
    matches = [line[3:] for line in read(f"/proc/{pid}/cgroup").splitlines() if line.startswith("0::")]
    require(len(matches) == 1, "unexpected cgroup v2 membership")
    return matches[0]


def identity(pid):
    status = read(f"/proc/{pid}/status")
    match = re.search(r"^NSpid:\s+([0-9]+)\s*$", status, re.MULTILINE)
    require(match is not None and int(match[1]) == pid, "worker must use the host PID namespace")
    uid = re.search(r"^Uid:[ \t]+([0-9]+)", status, re.MULTILINE)
    require(uid is not None, "worker real UID is unavailable")
    contents = read(f"/proc/{pid}/stat")
    fields = contents[contents.rfind(")") + 2:].split()
    return {"pid": pid, "uid": int(uid[1]), "proc_start_ticks": int(fields[19])}


def worker(group_name):
    require(GROUP_NAME.fullmatch(group_name), "invalid private group name")
    require(os.geteuid() != 0 and os.getegid() != 0, "worker must be unprivileged")
    if sys.stdin.buffer.read(1) != b"A":
        return 71
    group = ROOT / group_name
    require(memberships("self") == "/" + group_name, "worker is outside the chosen group")
    check_limits(group)
    require(read(group / "cgroup.procs").split() == [str(os.getpid())], "worker group is not a singleton")
    page = os.sysconf("SC_PAGE_SIZE")
    blocks = []
    for _ in range(MAX_BLOCKS):
        block = bytearray(1048576)
        for offset in range(0, len(block), page):
            block[offset] = 1
        blocks.append(block)
    return 72


def kernel_mount():
    info = ROOT.stat()
    device = f"{os.major(info.st_dev)}:{os.minor(info.st_dev)}"
    for line in read("/proc/self/mountinfo", 512 * 1024).splitlines():
        prefix, _, suffix = line.partition(" - ")
        if prefix.split()[2:5] == [device, "/", str(ROOT)] and suffix.startswith("cgroup2 "):
            return
    raise ValueError("expected a host-root cgroup v2 mount")


@contextlib.contextmanager
def private_group():
    available_memory()
    kernel_mount()
    require(read("/proc/sys/vm/panic_on_oom").strip() == "0",
            "kernel must already be configured to handle OOM without a panic")
    require({"memory", "pids"} <= set(read(ROOT / "cgroup.subtree_control").split()),
            "memory and pids controllers must already be enabled")
    group = ROOT / ("kit-a08b-oom-" + secrets.token_hex(8))
    group.mkdir(mode=0o755)
    try:
        group.chmod(0o755)
        for field, value in LIMITS.items():
            (group / field).write_text(value + "\n", encoding="ascii")
        check_limits(group)
        require(not read(group / "cgroup.procs").split(), "new private group has members")
        yield group
    finally:
        group.rmdir()


def observation(group, expected_pid):
    check_limits(group)
    members = read(group / "cgroup.procs").split()
    expected = [str(expected_pid)] if expected_pid is not None else []
    require(members == expected, "unexpected worker membership")
    require(memberships("self") != "/" + group.name, "observer must stay outside the worker group")
    info = group.stat()
    counters = {}
    for line in read(group / "memory.events.local").splitlines():
        key, value = line.split()
        require(key not in counters and value.isascii() and value.isdecimal(), "invalid memory event counter")
        counters[key] = int(value)
    require({"oom", "max", "oom_kill"} <= counters.keys(), "required local counters unavailable")
    require(members == read(group / "cgroup.procs").split(), "worker membership changed during observation")
    return {
        "device": info.st_dev, "inode": info.st_ino, "members": members,
        "memory_events_local": counters, "available_memory_bytes": available_memory(),
        "memory_peak_bytes": int(read(group / "memory.peak")),
    }


@contextlib.contextmanager
def kernel_log():
    descriptor = os.open("/dev/kmsg", os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISCHR(info.st_mode) and (os.major(info.st_rdev), os.minor(info.st_rdev)) == (1, 11),
                "expected the kernel message device")
        os.lseek(descriptor, 0, os.SEEK_END)
        yield descriptor
    finally:
        os.close(descriptor)


def kernel_hits(log, pid, group_name):
    group_path = "/" + group_name
    exact = []
    for _ in range(1024):
        try:
            record = os.read(log, 16384)
        except BlockingIOError:
            return exact
        fields, sep, text = record.partition(b";")
        header = fields.split(b",")
        require(sep and len(header) >= 4 and all(field.isdigit() for field in header[:3]),
                "unexpected kernel message framing")
        priority, sequence, usec = map(int, header[:3])
        if priority >> 3 or not text.startswith(b"oom-kill:constraint="):
            continue
        fields = dict(raw.split(b"=", 1) for raw in text.split(b"\n", 1)[0].split(b",") if b"=" in raw)
        if fields.get(b"pid") == str(pid).encode() or fields.get(b"oom_memcg") == group_path.encode():
            require(fields.get(b"pid") == str(pid).encode(), "unexpected local OOM victim identity")
            record = {
                "priority": priority, "sequence": sequence, "boot_microseconds": usec, "pid": pid,
                "constraint": fields[b"oom-kill:constraint"].decode("ascii"),
                "oom_memcg": fields.get(b"oom_memcg", b"").decode("ascii"),
                "task_memcg": fields.get(b"task_memcg", b"").decode("ascii"),
                "uid": int(fields[b"uid"]),
            }
            exact.append(record)
    raise ValueError("kernel observation exceeded its record budget")


def observe(group, case, uid, gid):
    with kernel_log() as log, subprocess.Popen(
        [sys.executable, "-I", "-S", str(Path(__file__).resolve()), "--worker", group.name],
        stdin=subprocess.PIPE, cwd="/", env={}, user=uid, group=gid, extra_groups=[],
    ) as process:
        pid = process.pid
        try:
            pidfd = os.pidfd_open(pid)
            try:
                (group / "cgroup.procs").write_text(str(pid) + "\n", encoding="ascii")
                expected = identity(pid)
                require(expected["uid"] == uid, "worker did not drop privilege")
                require(int(read(f"/proc/{pid}/oom_score_adj")) > -1000,
                        "worker must be eligible for the kernel OOM killer")
                require(memberships(pid) == "/" + group.name, "worker did not enter private group")
                before = observation(group, pid)
                require(identity(pid) == expected, "worker identity changed before release")
                if case == "memory_cap":
                    process.stdin.write(b"A")
                    process.stdin.flush()
                else:
                    signal.pidfd_send_signal(pidfd, signal.SIGKILL)
                exit_code = process.wait(timeout=15)
                after = observation(group, None)
                messages = kernel_hits(log, pid, group.name)
            finally:
                os.close(pidfd)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    require(exit_code == -signal.SIGKILL, "worker did not terminate by SIGKILL")
    require((before["device"], before["inode"]) == (after["device"], after["inode"]),
            "worker cgroup identity changed")
    original, final = before["memory_events_local"], after["memory_events_local"]
    require(original.keys() == final.keys(), "memory event counter schema changed")
    delta = {key: final[key] - old for key, old in original.items()}
    require(not any(value < 0 for value in delta.values()), "local counters reset")
    if case == "memory_cap":
        group_path = "/" + group.name
        require(delta["oom"] > 0 and delta["max"] > 0 and delta["oom_kill"] == 1
                and delta.get("oom_group_kill", 0) == 0, "local OOM counters disagree")
        require(len(messages) == 1 and messages[0]["constraint"] == "CONSTRAINT_MEMCG"
                and messages[0]["uid"] == expected["uid"]
                and messages[0]["oom_memcg"] == messages[0]["task_memcg"] == group_path,
                "kernel record does not independently identify this memory-cgroup victim")
    else:
        require(not any(delta.values()) and not messages, "ordinary signal had OOM evidence")
    return {
        "case": case, "group": "/" + group.name, "termination": exit_code, "worker": expected, "before": before,
        "after": after, "local_delta": delta, "kernel_messages": messages,
    }


def run(output, source_revision):
    require(sys.platform == "linux" and os.geteuid() == 0, "observer needs a disposable Linux VM with sudo")
    require(re.fullmatch(r"[0-9a-f]{40}", source_revision), "an exact source revision is required")
    uid, gid = int(os.environ["SUDO_UID"]), int(os.environ["SUDO_GID"])
    require(uid > 0 and gid > 0, "sudo caller must be unprivileged")
    require(not output.exists() and not output.is_symlink(), "select a new evidence path")
    start_boot = read("/proc/sys/kernel/random/boot_id")
    source = Path(__file__).read_bytes()
    observations = []
    for case in ("ordinary_sigkill", "memory_cap"):
        with private_group() as group:
            observations.append(observe(group, case, uid, gid))
        require(not group.exists(), "private cgroup cleanup failed")
    require(start_boot == read("/proc/sys/kernel/random/boot_id"), "kernel boot identity changed")
    require(Path(__file__).read_bytes() == source, "witness source changed during observation")
    evidence = {
        "evidence_version": 1, "kernel": os.uname().release, "boot_id": start_boot.strip(),
        "source_revision": source_revision, "observer_sha256": hashlib.sha256(source).hexdigest(),
        "verified_limits": LIMITS, "maximum_allocation_blocks": MAX_BLOCKS,
        "cases": observations, "cleanup_verified": True,
    }
    descriptor = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        os.fchown(file.fileno(), uid, gid)
        json.dump(evidence, file, indent=2, sort_keys=True)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        sys.exit(worker(sys.argv[2]))
    parser = argparse.ArgumentParser(description="Observe one bounded kernel cgroup OOM and one ordinary signal")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    arguments = parser.parse_args()
    run(arguments.output, arguments.source_revision)
