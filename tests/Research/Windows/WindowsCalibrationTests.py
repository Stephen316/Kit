import json as JsonCodec
import sys as System
from hashlib import sha256 as ShaDigest
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Calibration.BuildManifest import BuildManifest
from tests.Research.Calibration.RunCalibration import RunCalibration
from tests.Research.Windows.VerifyCalTrial import VerifyCalTrial

# the windows success fixture needs enough time for eight serial decoder sessions
KSerialTrialSeconds = 45


# a fixed workload is necessary to verify that windows reports decoder measurements without recommending restricted concurrency
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinSweep(TmpPath: FilePath) -> None:
    ManifestPath = BuildManifest(TmpPath, MaxSeconds=KSerialTrialSeconds)
    Manifest = JsonCodec.loads(ManifestPath.read_text(encoding="utf-8"))
    OutputPath = TmpPath / "Sweep"
    Report = RunCalibration(ManifestPath, OutputPath)
    assert Report["completed_sweep"] is True, Report
    assert Report["recommended_concurrency"] is None
    InputHash = Manifest["bindings"]["source:calibration"]["sha256"]
    for Requested in (1, 2, 4, 8):
        VerifyCalTrial(OutputPath / f"Trial{Requested}", InputHash)


# a rejected decoder must stop the private sweep and release its claims without forcing termination
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinReject(TmpPath: FilePath) -> None:
    ManifestPath = BuildManifest(TmpPath)
    Manifest = JsonCodec.loads(ManifestPath.read_text(encoding="utf-8"))
    InputPath = TmpPath / "Input.f3d"
    Content = b"invalid offline Fusion input"
    _ = InputPath.write_bytes(Content)
    Manifest["bindings"]["source:calibration"].update(
        sha256=ShaDigest(Content).hexdigest(), size_bytes=len(Content)
    )
    _ = ManifestPath.write_text(JsonCodec.dumps(Manifest), encoding="utf-8")
    OutputPath = TmpPath / "Rejected"
    Report = RunCalibration(ManifestPath, OutputPath, ExitCode=2)
    assert Report["completed_sweep"] is False
    assert Report["stop_reason"] == "child_did_not_complete", Report
    assert Report["recommended_concurrency"] is None
    TrialPath = OutputPath / "Trial1"
    Cleanup = JsonCodec.loads((TrialPath / "Cleanup.json").read_text(encoding="utf-8"))
    assert Cleanup["job_members_empty"] is True and not Cleanup["forced_groups"]
    assert Cleanup["claims_empty"] is True and Cleanup["sessions_empty"] is True
