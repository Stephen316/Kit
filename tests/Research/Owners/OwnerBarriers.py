import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import SessionHost


def WaitRecord(RecordPath: FilePath, OldDigest: str = "") -> dict[str, object]:
    Until = TimeClock.monotonic() + 45
    while TimeClock.monotonic() < Until:
        if RecordPath.is_file():
            try:
                Record: dict[str, object] = JsonCodec.loads(
                    RecordPath.read_text(encoding="utf-8")
                )
            except ValueError:
                continue
            if not OldDigest or Record.get("digest") != OldDigest:
                return Record
        TimeClock.sleep(0.02)
    raise AssertionError(f"owner process barrier did not arrive: {RecordPath.name}")


def WaitCompleted(Harness: SessionHost, JobNames: tuple[str, ...]) -> None:
    Until = TimeClock.monotonic() + 45
    while TimeClock.monotonic() < Until:
        JobValues = [Harness.ReadJob(JobName) for JobName in JobNames]
        if all(JobInfo["state"] == "completed" for JobInfo in JobValues):
            assert all(JobInfo["attempts"] == 1 for JobInfo in JobValues), JobValues
            return
        TimeClock.sleep(0.1)
    raise AssertionError("restarted supervisor did not complete current-owner jobs")
