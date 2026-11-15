import json as JsonCodec
import os as OsLayer
import signal as Signals
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


def RunChild() -> None:
    if System.platform != "win32":
        raise OSError("Windows child fixture requires a Windows host")
    _ = Signals.signal(Signals.SIGBREAK, Signals.SIG_IGN)
    RecordPath = FilePath(System.argv[2])
    _ = RecordPath.write_text(
        JsonCodec.dumps([int(System.argv[3]), OsLayer.getpid()]), encoding="utf-8"
    )
    TimeClock.sleep(120)
