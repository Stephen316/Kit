import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.SetAppRunner import SetAppRunner
from tests.Research.SupervisorClient import FixtureJob, SessionHost


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
        assert JobStatus["state"] == "waiting_application", JobStatus
        assert Harness.ReadJob("dependent")["state"] == "waiting_evidence"
        assert Harness.ReadJob("independent")["state"] == "completed"
        Result = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("absent")))
        assert Result["result"]["records"]["native_qualified"] is False
        assert "output_artifacts" not in Result
