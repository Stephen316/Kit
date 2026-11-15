import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.MemoryHost import MakeMemoryHost
from tests.Research.Supervisor.StopGroup import StopGroup
from tests.Research.SupervisorClient import FixtureJob, IsGoneByTimeout


# a real memory stop must reduce active capacity and reap the offending worker tree
def CheckMemBackoff() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeMemoryHost(RootPath)
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["adaptive_limits"] = True
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        ChildFile = RootPath / "Child.pid"
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "adaptive:memory",
                    "fixture.decode",
                    max_attempts=1,
                    options={"child_pid_path": str(ChildFile)},
                )
            ]
        )
        try:
            Events = JsonCodec.loads(JsonCodec.dumps(Harness.RunIdle()))
            Backoffs = [
                Event for Event in Events if Event.get("event") == "adaptive_backoff"
            ]
            assert len(Backoffs) == 1
            assert Backoffs[0]["adaptive_reason"] == "memory_limit"
            assert Backoffs[0]["target_limit"] == max(
                1, Backoffs[0]["before_limit"] // 2
            )
            assert Harness.ReadJob("adaptive:memory")["state"] == "failed"
            assert IsGoneByTimeout(int(ChildFile.read_text(encoding="ascii")))
        finally:
            if ChildFile.is_file():
                StopGroup(None, int(ChildFile.read_text(encoding="ascii")))
