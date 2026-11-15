import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Windows.SetWinRunnerMut import SetWinRunnerMut
from tests.Research.Windows.WaitForExit import WaitForExit
from tests.Research.Windows.WaitForPids import WaitForPids


@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinTree() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        SetWinRunnerMut(Harness)
        RecordPath = RootPath / "ProcessIds.json"
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "windows:tree",
                    "fixture.decode",
                    options={"mode": "exit", "pid_file": str(RecordPath)},
                )
            ]
        )
        _ = Harness.RunIdle(IdleSeconds=1)
        assert Harness.ReadJob("windows:tree")["state"] == "completed"
        for ProcessId in WaitForPids(RecordPath):
            WaitForExit(ProcessId)
