import hashlib as HashCodec
import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.Calibration.BuildManifest import BuildManifest
from tests.Research.Calibration.CheckTrial import CheckTrial
from tests.Research.Calibration.RunCalibration import RunCalibration


# a reader rejection must end the sweep instead of contaminating later throughput comparisons
def CheckBadDecode(TmpPath: FilePath) -> None:
    ManifestPath = BuildManifest(TmpPath)
    Manifest = JsonCodec.loads(ManifestPath.read_text(encoding="utf-8"))
    Content = b"not a native Fusion archive"
    _ = (TmpPath / "Input.f3d").write_bytes(Content)
    Manifest["bindings"]["source:calibration"].update(
        {"sha256": HashCodec.sha256(Content).hexdigest(), "size_bytes": len(Content)}
    )
    _ = ManifestPath.write_text(JsonCodec.dumps(Manifest), encoding="utf-8")
    OutputPath = TmpPath / "Failed"
    Report = RunCalibration(ManifestPath, OutputPath, ExitCode=2)
    assert (
        Report["completed_sweep"] is False and Report["recommended_concurrency"] is None
    )
    assert Report["stop_reason"] == "child_did_not_complete"
    CheckTrial(OutputPath / "Trial1", 1, TmpPath / "Input.f3d")
    assert not (OutputPath / "Trial2").exists()


# a trial deadline must stop remaining work before the sweep can recommend a limit
def CheckTimeout(TmpPath: FilePath) -> None:
    ManifestPath = BuildManifest(TmpPath, JobCount=256)
    Manifest = JsonCodec.loads(ManifestPath.read_text(encoding="utf-8"))
    Manifest["max_seconds"] = 5
    _ = ManifestPath.write_text(JsonCodec.dumps(Manifest), encoding="utf-8")
    OutputPath = TmpPath / "TimedOut"
    Report = RunCalibration(ManifestPath, OutputPath, ExitCode=2)
    assert (
        Report["completed_sweep"] is False and Report["recommended_concurrency"] is None
    )
    assert Report["stop_reason"] == "trial_timeout"
    CheckTrial(OutputPath / "Trial1", 1, TmpPath / "Input.f3d")
    assert not (OutputPath / "Trial2").exists()


# a reserve beyond available cores must prevent claims while retaining the refusal evidence
def CheckReserve(TmpPath: FilePath) -> None:
    ManifestPath = BuildManifest(TmpPath)
    Manifest = JsonCodec.loads(ManifestPath.read_text(encoding="utf-8"))
    Manifest["reserved_cpus"] = 65536
    _ = ManifestPath.write_text(JsonCodec.dumps(Manifest), encoding="utf-8")
    OutputPath = TmpPath / "Reserved"
    Report = RunCalibration(ManifestPath, OutputPath)
    assert (
        Report["completed_sweep"] is True and Report["recommended_concurrency"] is None
    )
    for Requested in (1, 2, 4, 8):
        TrialPath = OutputPath / f"Trial{Requested}"
        CheckTrial(TrialPath, Requested, TmpPath / "Input.f3d")
        Trial = JsonCodec.loads((TrialPath / "Trial.json").read_text(encoding="utf-8"))
        assert Trial["complete"] is False and Trial["completed_jobs"] == 0
        assert Trial["observed_peak_decode_concurrency"] == 0
        assert "cpu_headroom" in Trial["incomplete_reasons"]
