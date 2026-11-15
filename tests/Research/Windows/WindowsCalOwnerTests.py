import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Calibration.RunCalibration import KRepoRoot
from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Windows.CalOwnerCode import KCalOwnerCode
from tests.Research.Windows.SetWinRunner import SetWinRunner
from tests.Research.Windows.WaitForExit import WaitForExit


@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
@Pytest.mark.parametrize("ModeName", ["forced", "abrupt"])
def CheckCalOwner(TmpPath: FilePath, ModeName: str) -> None:
    Harness = SessionHost(TmpPath, {"decode": 1}, {"fixture.decode": "decode"})
    SetWinRunner(Harness)
    RecordPath = TmpPath / "ProcessIds.json"
    Harness.SubmitJobs(
        [
            FixtureJob(
                "windows:calibration",
                "fixture.decode",
                options={"mode": "hold", "pid_file": str(RecordPath)},
            )
        ]
    )
    Result = Subprocess.run(
        [
            System.executable,
            "-c",
            KCalOwnerCode,
            str(KRepoRoot),
            str(Harness.ConfigFile),
            str(RecordPath),
            ModeName,
        ],
        capture_output=True,
        text=True,
        timeout=50,
        check=False,
    )
    assert Result.returncode == (7 if ModeName == "abrupt" else 0), Result.stderr
    Observation = JsonCodec.loads(Result.stdout.splitlines()[0])
    assert Observation["bytes"] > 0 and len(set(Observation["pids"])) >= 3
    if ModeName == "forced":
        Receipt = JsonCodec.loads(Result.stdout.splitlines()[1])
        assert Receipt[0]["stopped"] is True
    for ProcessId in set(Observation["pids"]):
        WaitForExit(ProcessId)
