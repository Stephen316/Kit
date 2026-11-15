import signal as Signals
import os as OsLayer
import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


def StartChild(Options: dict[str, str]) -> None:
    if System.platform != "win32":
        raise OSError("Windows child fixture requires a Windows host")
    _ = Signals.signal(int(getattr(Signals, "SIGBREAK")), Signals.SIG_IGN)
    ChildProcess = Subprocess.Popen(
        [
            System.executable,
            "-m",
            "tests.Research.Windows.WindowsRunner",
            "child",
            Options["pid_file"],
            str(OsLayer.getpid()),
        ],
        creationflags=int(getattr(Subprocess, "CREATE_NEW_PROCESS_GROUP")),
    )
    UntilTime = TimeClock.monotonic() + 10
    while True:
        try:
            ProcessIds = JsonCodec.loads(
                FilePath(Options["pid_file"]).read_text(encoding="utf-8")
            )
            if ProcessIds == [OsLayer.getpid(), ChildProcess.pid]:
                break
        except (OSError, ValueError):
            pass
        if TimeClock.monotonic() >= UntilTime:
            raise RuntimeError("child did not report readiness")
        TimeClock.sleep(0.01)
    assert ChildProcess.poll() is None
    if Options["mode"] == "hold":
        TimeClock.sleep(120)
