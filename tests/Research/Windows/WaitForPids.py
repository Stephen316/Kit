import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath


def WaitForPids(RecordPath: FilePath) -> list[int]:
    UntilTime = TimeClock.monotonic() + 30
    while TimeClock.monotonic() < UntilTime:
        try:
            ProcessIds: list[int] = JsonCodec.loads(
                RecordPath.read_text(encoding="utf-8")
            )
            assert len(ProcessIds) == 2
            return ProcessIds
        except (OSError, ValueError):
            TimeClock.sleep(0.05)
    raise AssertionError("Windows runner did not record process identities")
