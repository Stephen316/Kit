import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest


# embedded windows process identity must work when the interpreter skips site packages
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinStart() -> None:
    SourceFile = (
        FilePath(__file__).resolve().parents[3]
        / "re/automation/ApplicationWorkers/WindowsIdentity.py"
    )
    Evidence = Subprocess.run(
        [
            System.executable,
            "-I",
            "-S",
            "-c",
            """import ctypes
from ctypes import wintypes
from importlib.util import find_spec
import os
import runpy
import subprocess
import sys

assert find_spec('win32api') is None and find_spec('pywintypes') is None
identity = runpy.run_path(sys.argv[1])
process_start = identity['process_start']
current_process = ctypes.WinDLL('kernel32').GetCurrentProcess
current_process.argtypes = []
current_process.restype = wintypes.HANDLE
assert process_start(os.getpid()) == identity['creation_time'](current_process())
assert process_start(0) is None

peer = subprocess.Popen(
    [sys.executable, '-I', '-S', '-c', 'import sys; sys.stdin.buffer.read()'],
    stdin=subprocess.PIPE,
)
try:
    started = process_start(peer.pid)
    assert started is not None and started.startswith('windows:')
    assert int(started.split(':')[1]) > 0 and process_start(peer.pid) == started
    try:
        process_start(peer.pid + (1 << 32))
    except OverflowError:
        pass
    else:
        raise AssertionError('out-of-range process ID was accepted')
finally:
    peer.stdin.close()
    peer.wait(timeout=10)

assert peer.returncode == 0 and process_start(peer.pid) is None
""",
            str(SourceFile),
        ],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert Evidence.returncode == 0, Evidence.stderr
