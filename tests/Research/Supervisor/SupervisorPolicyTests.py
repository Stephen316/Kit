import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.AdaptiveHost import MakeAdaptive
from tests.Research.SupervisorClient import FixtureJob


# numeric values must not silently activate or disable adaptive pool policy
def CheckPolicyBool() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = MakeAdaptive(FilePath(TempPath))
        Harness.SubmitJobs(
            [FixtureJob("adaptive:invalid", "fixture.decode", max_attempts=1)]
        )
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["adaptive_limits"] = 1
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        _ = Harness.RunCli("run", "--idle-seconds", "1", ExitCode=1)
        ConfigInfo["adaptive_limits"] = False
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        Blocked = Harness.ReadJob("adaptive:invalid")
        assert Blocked["state"] == "queued"
        assert Blocked["attempts"] == 0
