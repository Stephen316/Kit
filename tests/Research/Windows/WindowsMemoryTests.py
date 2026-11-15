import json as JsonCodec
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Windows.SetWinRunner import SetWinRunner
from tests.Research.Windows.WaitForExit import WaitForExit


@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinMemory() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        SetWinRunner(Harness, MemoryLimit=1)
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "windows:memory",
                    "fixture.decode",
                    max_attempts=1,
                    options={
                        "mode": "hold",
                        "pid_file": str(RootPath / "ProcessIds.json"),
                    },
                )
            ]
        )
        _ = Harness.RunIdle(IdleSeconds=1)
        JobInfo = Harness.ReadJob("windows:memory")
        assert JobInfo["state"] == "failed", JobInfo
        assert JobInfo["reason"] == "session stopped: memory_limit", JobInfo
        ReceiptInfo = JsonCodec.loads(
            JsonCodec.dumps(Harness.ReadResult("windows:memory"))
        )["receipt"]
        assert (
            ReceiptInfo["sampled_group_peak_memory_bytes"]
            > ReceiptInfo["memory_limit_bytes"]
        )
        WaitForExit(int(ReceiptInfo["pid"]))
