import os
import signal
import subprocess
import sys

from HostResources import group_memory
from Processes import group_running, process_start, stop_orphan
from Sessions import read_bounded

ENVIRONMENT = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ")


def start_supervisor(command, root, directory, stdout, stderr, pool):
    environment = {name: os.environ[name] for name in ENVIRONMENT if name in os.environ}
    environment.update({"HOME": str(directory), "TMPDIR": str(directory)})
    if sys.platform == "win32":
        from CalibrationWindows import CalibrationWindows

        process = CalibrationWindows(
            command, root, directory, environment, stdout, stderr, pool
        )
        return process, process.identity
    process = subprocess.Popen(
        command,
        cwd=root,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=subprocess.STDOUT if stderr is None else stderr,
        start_new_session=True,
        close_fds=True,
    )
    return process, process_start(process.pid)


def sample_workers(process, directory):
    if sys.platform == "win32":
        return process.sample_workers()
    leaders = set()
    for path in (directory / "State" / "sessions").glob("*/session.json"):
        try:
            record = read_bounded(path)
        except FileNotFoundError:
            continue
        if type(record.get("pid")) is int and process_start(
            record["pid"]
        ) == record.get("process_start"):
            leaders.add(record["pid"])
    return sum(group_memory(leaders).values())


def settle_supervisor(process, identity, stopping=False):
    if sys.platform == "win32":
        try:
            if process.poll() is None:
                if not stopping:
                    process.terminate()
                process.wait(timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            pass
        finally:
            forced = process.retire()
        return forced
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            return force_stop(process, identity)
    return []


def descendant_groups(pid):
    result = subprocess.run(
        ["/bin/ps", "-axo", "pid=,ppid=,pgid="],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        env={"PATH": "/bin:/usr/bin", "LC_ALL": "C"},
    )
    if result.returncode != 0 or len(result.stdout) > 4 * 1048576:
        raise OSError("owned process-tree measurement unavailable")
    rows = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 3 or any(not value.isdigit() for value in fields):
            raise OSError("owned process-tree measurement is invalid")
        rows.append(tuple(map(int, fields)))
    owned = {pid}
    while True:
        children = {child for child, parent, group in rows if parent in owned}
        if children <= owned:
            break
        owned.update(children)
        if len(owned) > 64:
            raise OSError("offline calibration process tree exceeds its declared limit")
    groups = {}
    for child, parent, group in rows:
        if child not in owned or child == pid or child != group:
            continue
        identity = process_start(child)
        if identity is None:
            if group_running(child):
                raise OSError("owned worker group creation identity is unavailable")
            continue
        groups[child] = identity
    return groups


def stop_groups(groups):
    receipts = []
    for pid, created in groups.items():
        stopped = stop_orphan(pid, created, 2)
        if not stopped and group_running(pid):
            raise OSError("an owned calibration worker group could not be stopped")
        receipts.append({"pid": pid, "process_start": created, "stopped": stopped})
    return receipts


def force_stop(process, identity):
    if sys.platform == "win32":
        return process.force_stop()
    if process.poll() is not None:
        return []
    if identity is None or process_start(process.pid) != identity:
        raise OSError("owned supervisor creation identity cannot be verified")
    os.kill(process.pid, signal.SIGSTOP)
    try:
        groups = descendant_groups(process.pid)
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)
        return stop_groups(groups)
    finally:
        if process.poll() is None:
            os.kill(process.pid, signal.SIGCONT)
