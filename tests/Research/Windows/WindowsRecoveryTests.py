import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Windows.SetWinRunner import SetWinRunner
from tests.Research.Windows.WaitForExit import WaitForExit
from tests.Research.Windows.WaitForPids import WaitForPids


@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinRestart() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        SetWinRunner(Harness)
        RecordPath = RootPath / "ProcessIds.json"
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "windows:restart",
                    "fixture.decode",
                    max_attempts=1,
                    options={"mode": "hold", "pid_file": str(RecordPath)},
                )
            ]
        )
        Running = Harness.StartRun("--max-seconds", "90")
        try:
            SessionInfo = Harness.WaitSession("windows:restart")
            assert str(SessionInfo["job_object"]).startswith("Local\\KitResearch-")
            _ = Harness.RunCli("run", "--idle-seconds", "1", ExitCode=4)
            ProcessIds = WaitForPids(RecordPath)
            Running.kill()
            _ = Running.communicate(timeout=30)
            for ProcessId in ProcessIds:
                WaitForExit(ProcessId)
            Events = Harness.RunIdle(IdleSeconds=1)
            assert any("orphan" in str(EventInfo) for EventInfo in Events)
            assert Harness.ReadJob("windows:restart")["state"] == "failed"
        finally:
            if Running.poll() is None:
                Running.kill()
            _ = Running.communicate(timeout=30)
