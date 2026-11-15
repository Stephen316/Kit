import json as JsonCodec
import sqlite3 as Sqlite
import tempfile as TempFiles
from contextlib import closing as CloseConnection
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.SetAppRunner import SetAppRunner
from tests.Research.SupervisorClient import FixtureJob, SessionHost


# unsupported application work must wait without blocking unrelated jobs or publishing unearned native evidence
@TestMark.parametrize("Application", ("fusion", "solidworks"))
def CheckParking(Application: str) -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Queue = DispatchHost(RootPath)
        Config = JsonCodec.loads(Queue.ConfigFile.read_text(encoding="utf-8"))
        Config.update(
            {"application": Application, "endpoint": str(RootPath / "Missing")}
        )
        _ = Queue.ConfigFile.write_text(JsonCodec.dumps(Config), encoding="utf-8")
        Harness = SessionHost(
            RootPath,
            {"apps": 1, "decode": 1},
            {"fixture.app": "apps", "fixture.decode": "decode"},
        )
        SetAppRunner(Harness, Queue.ConfigFile)
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "absent",
                    "fixture.app",
                    lease_seconds=30,
                    resources=["application:missing"],
                    options={"phase": "a"},
                ),
                FixtureJob("dependent", "fixture.decode", depends_on=["absent"]),
                FixtureJob("independent", "fixture.decode"),
            ]
        )
        _ = Harness.RunIdle()
        JobStatus = Harness.ReadJob("absent")
        assert JobStatus["state"] == "waiting_application", JobStatus["reason"]
        assert Harness.ReadJob("dependent")["state"] == "waiting_evidence"
        assert Harness.ReadJob("independent")["state"] == "completed"
        Result = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("absent")))
        assert Result["result"]["records"]["native_qualified"] is False
        assert "output_artifacts" not in Result
        VerifyOccupancy(Harness)


# clipping to the known durable claim interval isolates the exact ownership time
def OccupiedWindow(Harness: SessionHost) -> list[str]:
    assert Harness.StorePath is not None
    DatabasePath = Harness.StorePath / "ledger.sqlite3"
    with CloseConnection(
        Sqlite.connect(DatabasePath.as_uri() + "?mode=ro", uri=True)
    ) as Database:
        Times = Database.execute(
            "SELECT started,ended FROM attempts WHERE job_id=?", ("absent",)
        ).fetchone()
    assert Times is not None
    Started, Ended = float(Times[0]), float(Times[1])
    assert 0 < Started < Ended
    Margin = (Ended - Started) / 4
    return [
        "status",
        "--claim-occupancy",
        "application:missing",
        str(Started + Margin),
        str(Ended - Margin),
    ]


# a replaced job definition cannot erase occupancy charged to its original application resource
def VerifyOccupancy(Harness: SessionHost) -> None:
    Arguments = OccupiedWindow(Harness)
    Default = JsonCodec.loads(Harness.RunCli("status"))
    assert set(Default) == {"pools"}
    Report = JsonCodec.loads(Harness.RunCli(*Arguments))["claim_occupancy"]
    assert Report["scope"] == "a03_recorded_claim_occupancy"
    assert Report["recorded_closed_claims"] == 1
    assert Report["recorded_open_claims"] == 0
    assert Report["resource_available_at_observation"] is False
    assert Report["occupied_seconds"] == Report["window_seconds"] > 0
    assert Report["occupancy"] == 1.0
    Harness.SubmitJobs([FixtureJob("absent", "fixture.app", options={"phase": "a"})])
    assert JsonCodec.loads(Harness.RunCli(*Arguments))["claim_occupancy"] == Report
