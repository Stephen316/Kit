# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest


# a disposable pipe blocked child supplies the real kernel exit boundary
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckHeldExit() -> None:
    Workers = (
        FilePath(__file__).resolve().parents[4] / "re/automation/ApplicationWorkers"
    )
    Evidence = Subprocess.run(
        [
            System.executable,
            "-I",
            "-B",
            "-S",
            "-c",
            """from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from importlib.util import find_spec
from pathlib import Path
import subprocess
import sys
from threading import Event
from unittest.mock import patch

assert find_spec("win32api") is None and find_spec("pywintypes") is None
workers = Path(sys.argv[1])
sys.path.insert(0, str(workers))
from WindowsIdentity import process_start
import WindowsProcessExit as exit_tool
from WindowsProcessExit import observe_exit, watch_peer

def refuse(action, expected):
    try:
        action()
    except ValueError as error:
        assert expected in str(error), error
    else:
        raise AssertionError(expected)

def arm(peer, image):
    with watch_peer(peer, image):
        pass

def race_close(owner, watch, child):
    waiting, close_requested, contended, signaled = Event(), Event(), Event(), Event()
    kernel_wait, kernel_close = exit_tool.WAIT_FOR_OBJECT, exit_tool.CLOSE_HANDLE
    mutex = watch._lock

    class TrackedLock:
        def __enter__(self):
            if close_requested.is_set():
                contended.set()
            mutex.acquire()

        def __exit__(self, *_):
            mutex.release()

    def wait_for_exit(handle, timeout):
        waiting.set()
        status = kernel_wait(handle, timeout)
        signaled.set()
        return status

    def close_handle(handle):
        assert signaled.is_set(), "the handle closed during its native wait"
        return kernel_close(handle)

    def close_watch():
        close_requested.set()
        owner.close()

    with patch.object(watch, "_lock", TrackedLock()), patch.object(
        exit_tool, "WAIT_FOR_OBJECT", wait_for_exit
    ), patch.object(exit_tool, "CLOSE_HANDLE", close_handle), ThreadPoolExecutor(2) as threads:
        observation = threads.submit(observe_exit, watch, 10_000)
        try:
            assert waiting.wait(2), "the observer did not enter its kernel wait"
            closure = threads.submit(close_watch)
            assert contended.wait(2), "context exit did not contend for the held handle"
            assert not closure.done(), "context exit did not wait for the observer"
        finally:
            child.stdin.close()
        evidence = observation.result(timeout=8)
        closure.result(timeout=8)
    return evidence

executable = Path(sys.executable).resolve(strict=True)
child = subprocess.Popen(
    [str(executable), "-I", "-S", "-c", "import sys; sys.stdin.buffer.read(); raise SystemExit(37)"],
    stdin=subprocess.PIPE,
)
try:
    started = process_start(child.pid)
    assert isinstance(started, str) and started.startswith("windows:")
    peer = {"pid": child.pid, "started": started}
    tick = int(started.split(":")[1])
    refuse(lambda: arm({**peer, "started": f"windows:{tick+1}"}, executable), "creation identity differs")
    refuse(lambda: arm(peer, workers / "WindowsIdentity.py"), "image or owner session differs")
    with ExitStack() as owner:
        watch = owner.enter_context(watch_peer(peer, executable))
        assert observe_exit(watch, 0) is None
        refuse(lambda: observe_exit(watch, -1), "wait must be between")
        record = race_close(owner, watch, child)
        assert record is not None and record["exit_filetime"] >= tick
        assert record == {
            "observation": "windows_process_exit_handle", **peer,
            "exit_filetime": record["exit_filetime"], "exit_code": 37,
        }
    refuse(lambda: observe_exit(watch, 0), "watch is closed")
    assert child.wait(timeout=10) == 37
    try:
        arm(peer, executable)
    except ValueError as error:
        assert "exited before" in str(error) or "handle is unavailable" in str(error)
    else:
        raise AssertionError("an exited peer could arm a new watch")
finally:
    if not child.stdin.closed:
        child.stdin.close()
    child.wait(timeout=10)
""",
            str(Workers),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=40,
    )
    assert Evidence.returncode == 0, Evidence.stderr
