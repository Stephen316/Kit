import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.AdaptiveHost import MakeAdaptive
from tests.Research.SupervisorClient import FixtureJob


def CheckLowReserve() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = MakeAdaptive(FilePath(TempPath))
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["reserved_memory_mib"] = 1048576
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        Harness.SubmitJobs(
            [FixtureJob("adaptive:reserve", "fixture.decode", max_attempts=1)]
        )
        Events = JsonCodec.loads(JsonCodec.dumps(Harness.RunIdle(IdleSeconds=2)))
        Admissions = [Event for Event in Events if Event.get("event") == "admission"]
        assert len(Admissions) == 1
        assert Admissions[0]["adaptive_reason"] == "memory_headroom"
        assert Admissions[0]["active_limit"] == 0
        assert (
            Admissions[0]["host"]["available_memory_bytes"]
            < Admissions[0]["reserved_memory_bytes"]
        )
        Blocked = Harness.ReadJob("adaptive:reserve")
        assert Blocked["state"] == "queued"
        assert Blocked["attempts"] == 0
