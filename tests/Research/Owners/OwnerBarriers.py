import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import SessionHost


# restart checks need a fresh durable observation before accepting that an ownership phase has changed
def WaitRecord(RecordPath: FilePath) -> dict[str, object]:
    Until = TimeClock.monotonic() + 45
    while TimeClock.monotonic() < Until:
        if RecordPath.is_file():
            try:
                Record: dict[str, object] = JsonCodec.loads(
                    RecordPath.read_text(encoding="utf-8")
                )
            except ValueError:
                continue
            return Record
        TimeClock.sleep(0.02)
    raise AssertionError(f"owner process barrier did not arrive: {RecordPath.name}")


# immutable owner publications keep replacement registration independent of the old record reader
def WaitOwner(GateRoot: FilePath, OldDigest: str = "") -> dict[str, object]:
    Until = TimeClock.monotonic() + 45
    while TimeClock.monotonic() < Until:
        Candidates = [
            RecordPath
            for RecordPath in GateRoot.glob("Owner-*.json")
            if RecordPath.name != f"Owner-{OldDigest}.json"
        ]
        if Candidates:
            (RecordPath,) = Candidates
            Record: dict[str, object] = JsonCodec.loads(RecordPath.read_bytes())
            assert RecordPath.name == f"Owner-{Record['digest']}.json"
            return Record
        TimeClock.sleep(0.02)
    raise AssertionError("replacement owner process barrier did not arrive")


# replacement execution must be observed through durable job states before checking the obsolete process
def WaitCompleted(Harness: SessionHost, JobNames: tuple[str, ...]) -> None:
    Until = TimeClock.monotonic() + 45
    while TimeClock.monotonic() < Until:
        JobValues = [Harness.ReadJob(JobName) for JobName in JobNames]
        if all(JobInfo["state"] == "completed" for JobInfo in JobValues):
            assert all(JobInfo["attempts"] == 1 for JobInfo in JobValues), JobValues
            return
        TimeClock.sleep(0.1)
    raise AssertionError("restarted supervisor did not complete current-owner jobs")
