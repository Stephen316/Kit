import json as JsonCodec
import sqlite3 as SqlCodec
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import FixtureJob, SessionHost


def BatchJobs(CountJobs: int, **Settings: object) -> list[dict[str, object]]:
    return [
        FixtureJob(
            f"batch:{Index:02d}",
            "fixture.decode",
            inputs={"source": "source"},
            **Settings,
        )
        for Index in range(CountJobs)
    ]


def BatchEvents(Events: list[object], EventName: str) -> list[dict[str, object]]:
    Records: list[dict[str, object]] = [
        JsonCodec.loads(JsonCodec.dumps(Event)) for Event in Events
    ]
    return [Record for Record in Records if Record.get("event") == EventName]


def CheckBatchData(Harness: SessionHost, CountJobs: int) -> None:
    for Index in range(CountJobs):
        JobName = f"batch:{Index:02d}"
        assert Harness.ReadJob(JobName)["state"] == "completed"
        ResultInfo = Harness.ReadResult(JobName)
        Normalized = JsonCodec.loads(JsonCodec.dumps(ResultInfo))
        Artifact = Normalized["output_artifacts"]["answer"]
        assert Harness.StorePath is not None
        ObjectPath = (
            Harness.StorePath / "objects" / Artifact["sha256"][:2] / Artifact["sha256"]
        )
        assert ObjectPath.read_bytes() == JobName.encode("ascii")
        assert Normalized["result"]["records"]["tokenless"] is True
        assert Normalized["receipt"]["job_id"] == JobName
        assert not list((Harness.RootPath / "SupervisorState" / "claims").iterdir())


def ReadSoloMarks(RootPath: FilePath) -> list[tuple[str, int, str]]:
    with SqlCodec.connect(RootPath / "Store" / "ledger.sqlite3") as Database:
        return list(
            Database.execute(
                "SELECT job_id,generation,fingerprint FROM group_solo ORDER BY job_id"
            )
        )
