import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import FixtureJob, SessionHost


# configured memory reserves must protect other work without spending an attempt
def CheckMemReserve() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["reserved_memory_mib"] = 1048576
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        Harness.SubmitJobs(
            [FixtureJob("budget:memory", "fixture.decode", max_attempts=1)]
        )
        Events = JsonCodec.loads(JsonCodec.dumps(Harness.RunIdle(IdleSeconds=1)))
        Admissions = [Event for Event in Events if Event.get("event") == "admission"]
        assert len(Admissions) == 1
        assert Admissions[0]["reason"] == "memory headroom"
        Blocked = Harness.ReadJob("budget:memory")
        assert Blocked["state"] == "queued"
        assert Blocked["attempts"] == 0
