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
            """from importlib.util import find_spec
from pathlib import Path
import subprocess
import sys

assert find_spec("win32api") is None and find_spec("pywintypes") is None
workers = Path(sys.argv[1])
sys.path.insert(0, str(workers))
from WindowsIdentity import process_start
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
    with watch_peer(peer, executable) as watch:
        assert observe_exit(watch, 0) is None
        refuse(lambda: observe_exit(watch, -1), "wait must be between")
        child.stdin.close()
        record = observe_exit(watch, 10_000)
        assert record is not None and record["exit_filetime"] >= tick
        assert record == {
            "observation": "windows_process_exit_handle", **peer,
            "exit_filetime": record["exit_filetime"], "exit_code": 37,
        }
        assert observe_exit(watch, 0) == record
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
