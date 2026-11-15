import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath


def WaitSession(OutputPath: FilePath) -> dict[str, object]:
    Until = TimeClock.monotonic() + 30
    while TimeClock.monotonic() < Until:
        for RecordPath in (OutputPath / "Trial1" / "State" / "sessions").glob(
            "*/session.json"
        ):
            try:
                Record: dict[str, object] = JsonCodec.loads(
                    RecordPath.read_text(encoding="utf-8")
                )
                return Record
            except FileNotFoundError:
                continue
        TimeClock.sleep(0.05)
    raise AssertionError("no actual offline decoder session started")
