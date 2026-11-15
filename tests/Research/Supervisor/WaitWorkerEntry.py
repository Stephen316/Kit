import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath


def WaitWorkerEntry(
    RootPath: FilePath, SessionName: str, ProcessId: int, PhaseName: str
) -> None:
    EntryFile = (
        RootPath
        / "SupervisorState"
        / "sessions"
        / SessionName
        / f"{PhaseName}.entered.json"
    )
    Until = TimeClock.monotonic() + 30
    while TimeClock.monotonic() < Until:
        if EntryFile.is_file():
            EntryInfo = JsonCodec.loads(EntryFile.read_text(encoding="utf-8"))
            assert EntryInfo == {"pid": ProcessId, "phase": PhaseName}
            return
        TimeClock.sleep(0.02)
    raise AssertionError(f"worker did not enter its {PhaseName} execution phase")
