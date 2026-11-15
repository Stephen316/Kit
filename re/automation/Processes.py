import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def process_start(pid):
    if type(pid) is not int or pid <= 1:
        return None
    if sys.platform.startswith("linux"):
        try:
            content = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        except (OSError, UnicodeDecodeError):
            return None
        fields = content[content.rindex(")") + 2:].split()
        return f"linux:{fields[19]}" if len(fields) > 19 else None
    try:
        result = subprocess.run(["/bin/ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True, timeout=10, check=False, env={"LC_ALL": "C", "PATH": "/bin:/usr/bin"})
    except (OSError, subprocess.SubprocessError):
        return None
    text = " ".join(result.stdout.split())
    return f"ps:{text}" if result.returncode == 0 and text else None


def signal_group(pid, number):
    try:
        os.killpg(pid, number)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def group_alive(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def group_running(pid):
    if not group_alive(pid):
        return False
    try:
        result = subprocess.run(["/bin/ps", "-axo", "pgid=,stat="], capture_output=True, text=True, timeout=10, check=False, env={"LC_ALL": "C", "PATH": "/bin:/usr/bin"})
    except (OSError, subprocess.SubprocessError):
        return True
    if result.returncode != 0:
        return True
    return any(fields[0] == str(pid) and not fields[1].startswith("Z") for line in result.stdout.splitlines() if len(fields := line.split()) >= 2)


def stop_orphan(pid, start, grace):
    if process_start(pid) != start:
        return False
    signal_group(pid, signal.SIGTERM)
    until = time.monotonic() + grace
    while group_running(pid) and time.monotonic() < until:
        time.sleep(0.1)
    if group_running(pid):
        current = process_start(pid)
        if current is not None and current != start:
            return False
        signal_group(pid, signal.SIGKILL)
        until = time.monotonic() + 5
        while group_running(pid) and time.monotonic() < until:
            time.sleep(0.1)
    return not group_running(pid)


def peak_bytes(usage):
    return usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)


def stderr_tail(path, limit=2048):
    try:
        with Path(path).open("rb") as source:
            size = source.seek(0, os.SEEK_END)
            source.seek(max(0, size - limit * 4))
            return source.read().decode("utf-8", "replace")[-limit:]
    except OSError:
        return ""
