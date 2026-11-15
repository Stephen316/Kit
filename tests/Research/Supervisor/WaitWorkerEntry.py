import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath


def WaitWorkerEntry(RootPath: FilePath, SessionName: str, ProcessId: int) -> None:
    EntryFile = (
        RootPath
        / "SupervisorState"
        / "sessions"
        / SessionName
        / "sleep-first.entered.json"
    )
    Until = TimeClock.monotonic() + 30
    while TimeClock.monotonic() < Until:
        if EntryFile.is_file():
            EntryInfo = JsonCodec.loads(EntryFile.read_text(encoding="utf-8"))
            assert EntryInfo == {"pid": ProcessId, "phase": "sleep-first"}
            return
        TimeClock.sleep(0.02)
    raise AssertionError("sleep-first worker did not enter its live execution phase")
