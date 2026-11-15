import json as JsonCodec
import os as OsLayer
import signal as SignalApi
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Calibration.BuildManifest import BuildManifest
from tests.Research.Calibration.CheckTrial import CheckTrial
from tests.Research.Calibration.RunCalibration import KRepoRoot
from tests.Research.Calibration.ResumeOwned import ResumeOwned
from tests.Research.Calibration.WaitSession import WaitSession
from tests.Research.SupervisorClient import IsGoneByTimeout


def CheckInterrupt(TmpPath: FilePath) -> None:
    ManifestPath = BuildManifest(TmpPath, JobCount=256)
    OutputPath = TmpPath / "Interrupted"
    Process = Subprocess.Popen(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Calibration.py"),
            "--manifest",
            str(ManifestPath),
            "--output",
            str(OutputPath),
        ],
        stdout=Subprocess.PIPE,
        stderr=Subprocess.PIPE,
        text=True,
    )
    try:
        Session = WaitSession(OutputPath)
        Process.terminate()
        Output, ErrorText = Process.communicate(timeout=60)
        assert Process.returncode == 2, Output + ErrorText
        Report = JsonCodec.loads(
            (OutputPath / "Calibration.json").read_text(encoding="utf-8")
        )
        assert Report["stop_reason"] == "interrupted"
        assert (
            Report["completed_sweep"] is False
            and Report["recommended_concurrency"] is None
        )
        CheckTrial(OutputPath / "Trial1", 1, TmpPath / "Input.f3d")
        assert IsGoneByTimeout(CastValue(int, Session["pid"]))
    finally:
        if Process.poll() is None:
            Process.terminate()
            _ = Process.communicate(timeout=60)


def CheckFrozenStop(TmpPath: FilePath) -> None:
    ManifestPath = BuildManifest(TmpPath, JobCount=256)
    OutputPath = TmpPath / "Frozen"
    Process = Subprocess.Popen(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Calibration.py"),
            "--manifest",
            str(ManifestPath),
            "--output",
            str(OutputPath),
        ],
        stdout=Subprocess.PIPE,
        stderr=Subprocess.PIPE,
        text=True,
    )
    Owner: dict[str, object] = {}
    try:
        _ = WaitSession(OutputPath)
        Owner = JsonCodec.loads(
            (OutputPath / "Trial1" / "SupervisorProcess.json").read_text(
                encoding="utf-8"
            )
        )
        OsLayer.kill(CastValue(int, Owner["pid"]), SignalApi.SIGSTOP)
        Process.terminate()
        Output, ErrorText = Process.communicate(timeout=90)
        assert Process.returncode == 2, Output + ErrorText
        Cleanup = JsonCodec.loads(
            (OutputPath / "Trial1" / "Cleanup.json").read_text(encoding="utf-8")
        )
        assert Cleanup["forced_groups"]
        assert Cleanup["sessions_empty"] is True and Cleanup["claims_empty"] is True
        assert IsGoneByTimeout(CastValue(int, Owner["pid"]))
    finally:
        if Process.poll() is None:
            if Owner:
                ResumeOwned(
                    CastValue(int, Owner["pid"]), CastValue(str, Owner["process_start"])
                )
            Process.terminate()
            _ = Process.communicate(timeout=60)
