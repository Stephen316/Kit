import os
import signal
import subprocess

from Processes import group_running, process_start, stop_orphan


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
