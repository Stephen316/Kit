import signal as Signals
import os as OsLayer
import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


def StartChild(Options: dict[str, str]) -> None:
    _ = Signals.signal(Signals.SIGBREAK, Signals.SIG_IGN)
    ChildProcess = Subprocess.Popen(
        [
            System.executable,
            "-m",
            "tests.Research.Windows.WindowsRunner",
            "child",
            Options["pid_file"],
            str(OsLayer.getpid()),
        ],
        creationflags=Subprocess.CREATE_NEW_PROCESS_GROUP,
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
