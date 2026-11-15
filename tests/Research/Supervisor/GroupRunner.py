import os as OsLayer
import signal as Signals
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


# shutdown needs a real descendant that ignores graceful termination to prove group reaping
def StartGroup() -> None:
    Reader, Writer = OsLayer.pipe()
    ChildId = OsLayer.fork()
    if ChildId == 0:
        OsLayer.close(Reader)
        _ = Signals.signal(Signals.SIGTERM, Signals.SIG_IGN)
        _ = OsLayer.write(Writer, b"ready")
        OsLayer.close(Writer)
        TimeClock.sleep(120)
        OsLayer._exit(0)
    OsLayer.close(Writer)
    assert OsLayer.read(Reader, 5) == b"ready"
    OsLayer.close(Reader)
    ChildFile = FilePath(System.argv[1]) / "work" / "child.pid"
    _ = ChildFile.with_suffix(".pending").write_text(str(ChildId), encoding="ascii")
    _ = ChildFile.with_suffix(".pending").replace(ChildFile)
    TimeClock.sleep(120)


if __name__ == "__main__":
    StartGroup()
