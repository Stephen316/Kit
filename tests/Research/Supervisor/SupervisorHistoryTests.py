import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.LearningHost import MakeLearnHost
from tests.Research.SupervisorClient import FixtureJob


# unrecognized persistent memory history must stop admission before a lease is consumed
def CheckBadHistory() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeLearnHost(RootPath)
        Harness.SubmitJobs(
            [FixtureJob("history:blocked", "fixture.decode", max_attempts=1)]
        )
        StatePath = RootPath / "SupervisorState"
        StatePath.mkdir()
        _ = (StatePath / "memory-history.json").write_text(
            JsonCodec.dumps({"history_version": 3, "records": []}), encoding="utf-8"
        )
        _ = Harness.RunCli("run", "--idle-seconds", "1", ExitCode=1)
        Blocked = Harness.ReadJob("history:blocked")
        assert Blocked["state"] == "queued"
        assert Blocked["attempts"] == 0
