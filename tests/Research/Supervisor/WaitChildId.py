import time as TimeClock
from pathlib import Path as FilePath


def WaitChildId(RootPath: FilePath, SessionName: str) -> int:
    ChildFile = (
        RootPath / "SupervisorState" / "sessions" / SessionName / "work/child.pid"
    )
    UntilTime = TimeClock.monotonic() + 15
    while not ChildFile.is_file() and TimeClock.monotonic() < UntilTime:
        TimeClock.sleep(0.05)
    return int(ChildFile.read_text(encoding="ascii"))
