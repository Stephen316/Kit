import sys as System
import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Windows.SetWinRunner import SetWinRunner
from tests.Research.Windows.WaitForExit import WaitForExit
from tests.Research.Windows.WaitForPids import WaitForPids


@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinTree() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        SetWinRunner(Harness)
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
        Events = Harness.RunIdle(IdleSeconds=1)
        JobInfo = Harness.ReadJob("windows:tree")
        if JobInfo["state"] != "completed":
            print(
                JsonCodec.dumps({"job": JobInfo, "events": Events}, sort_keys=True),
                flush=True,
            )
        assert JobInfo["state"] == "completed", {"job": JobInfo, "events": Events}
        for ProcessId in WaitForPids(RecordPath):
            WaitForExit(ProcessId)
