import json as JsonCodec
import os as OsLayer
import signal as Signals
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


# a persistent descendant is needed to verify that custody survives launcher and leader transitions
def RunChild() -> None:
    if System.platform != "win32":
        raise OSError("Windows child fixture requires a Windows host")
    _ = Signals.signal(int(getattr(Signals, "SIGBREAK")), Signals.SIG_IGN)
    RecordPath = FilePath(System.argv[2])
    _ = RecordPath.write_text(
        JsonCodec.dumps(
            {
                "caller_pid": int(System.argv[3]),
                "application_pid": OsLayer.getpid(),
                "parent_pid": OsLayer.getppid(),
            }
        ),
        encoding="utf-8",
    )
    TimeClock.sleep(120)
