import json as JsonCodec
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Windows.SetWinRunner import SetWinRunner
from tests.Research.Windows.WaitForExit import WaitForExit
from tests.Research.Windows.WaitForPids import WaitForPids


# a retained file must not give an exited supervisor a live decision or be changed by status
def VerifyLostCap(Harness: SessionHost) -> None:
    Snapshot = Harness.RootPath / "SupervisorState" / "supervisor-capacity.json"
    SnapshotBytes = Snapshot.read_bytes()
    Abandoned = JsonCodec.loads(Harness.RunCli("status"))["pools"]["decode"]
    assert Abandoned["capacity"] == {"state": "unavailable", "decision": None}
    assert Snapshot.read_bytes() == SnapshotBytes


# windows supervisor restart must retire the exact owned worker tree and settle its abandoned claim
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
            LivePool = JsonCodec.loads(Harness.RunCli("status"))["pools"]["decode"]
            assert LivePool["capacity"]["decision"]["active_limit"] == 1
            ProcessIds = WaitForPids(RecordPath)
            Running.kill()
            _ = Running.communicate(timeout=30)
            for ProcessId in ProcessIds:
                WaitForExit(ProcessId)
            VerifyLostCap(Harness)
            Events = Harness.RunIdle(IdleSeconds=1)
            assert any("orphan" in str(EventInfo) for EventInfo in Events)
            assert Harness.ReadJob("windows:restart")["state"] == "failed"
        finally:
            if Running.poll() is None:
                Running.kill()
            _ = Running.communicate(timeout=30)
