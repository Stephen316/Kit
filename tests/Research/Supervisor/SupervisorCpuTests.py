import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import FixtureJob, SessionHost


def CheckCpuReserve() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["reserved_cpus"] = 65536
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        Harness.SubmitJobs([FixtureJob("budget:cpu", "fixture.decode", max_attempts=1)])
        Events = JsonCodec.loads(JsonCodec.dumps(Harness.RunIdle(IdleSeconds=1)))
        Admissions = [Event for Event in Events if Event.get("event") == "admission"]
        assert len(Admissions) == 1
        assert Admissions[0]["reason"] == "cpu headroom"
        assert Admissions[0]["additional_sessions"] == 0
        Blocked = Harness.ReadJob("budget:cpu")
        assert Blocked["state"] == "queued"
        assert Blocked["attempts"] == 0
        ConfigInfo["reserved_cpus"] = 0
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        _ = Harness.RunIdle()
        assert Harness.ReadJob("budget:cpu")["state"] == "completed"
