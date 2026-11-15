import json as JsonCodec
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Supervisor.WatchLogFiles import WatchLogFiles


def CheckNoisyLogs() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        RegistryFile = RootPath / "Runners.json"
        Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
        Registry["runners"]["fixture.decode"]["argv"] = [
            System.executable,
            str(FilePath(__file__).with_name("NoiseRunner.py")),
            "{session}",
        ]
        _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["max_log_bytes"] = 8192
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        Harness.SubmitJobs([FixtureJob("noise:logs", "fixture.decode", max_attempts=1)])
        Running = Harness.StartRun("--idle-seconds", "3", "--max-seconds", "60")
        try:
            SessionInfo = Harness.WaitSession("noise:logs")
            SessionPath = (
                RootPath / "SupervisorState" / "sessions" / str(SessionInfo["session"])
            )
            WatchLogFiles(Running, SessionPath)
        finally:
            Running.kill()
            _ = Running.wait()
        Stored = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("noise:logs")))
        assert Harness.ReadJob("noise:logs")["state"] == "completed"
        for StreamName in ("stdout", "stderr"):
            assert Stored["receipt"]["logs"][StreamName] == {
                "limit_bytes": 8192,
                "seen_bytes": 2097152,
                "retained_bytes": 8192,
                "dropped_bytes": 2088960,
            }
