import signal as Signals
import os as OsLayer
import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.Windows.BindChild import BindChild


# tree cleanup checks need a bound descendant that stays alive until the owner retires it
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
            Options["pid_file"] + ".ready",
            str(OsLayer.getpid()),
        ],
        creationflags=int(getattr(Subprocess, "CREATE_NEW_PROCESS_GROUP")),
    )
    UntilTime = TimeClock.monotonic() + 10
    Observation: dict[str, int] = {}
    JobName = ""
    while True:
        try:
            Observation = JsonCodec.loads(
                FilePath(Options["pid_file"] + ".ready").read_text(encoding="utf-8")
            )
            JobName = JsonCodec.loads(
                (FilePath(OsLayer.environ["KIT_SESSION"]) / "session.json").read_text(
                    encoding="utf-8"
                )
            )["job_object"]
            break
        except (OSError, ValueError):
            pass
        if TimeClock.monotonic() >= UntilTime:
            raise RuntimeError("child did not report readiness")
        TimeClock.sleep(0.01)
    assert ChildProcess.poll() is None
    ProcessIds = BindChild(ChildProcess.pid, OsLayer.getpid(), Observation, JobName)
    _ = FilePath(Options["pid_file"]).write_text(
        JsonCodec.dumps(ProcessIds), encoding="utf-8"
    )
    if Options["mode"] == "hold":
        TimeClock.sleep(120)
