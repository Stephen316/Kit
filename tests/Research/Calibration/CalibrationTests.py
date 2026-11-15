import json as JsonCodec
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Calibration.BuildManifest import BuildManifest
from tests.Research.Calibration.CheckTrial import CheckTrial
from tests.Research.Calibration.RunCalibration import RunCalibration


# a constrained sweep must retain physical observations without claiming it reached requested overlap
def CheckSweep(TmpPath: FilePath) -> None:
    ManifestPath = BuildManifest(TmpPath)
    OutputPath = TmpPath / "Sweep"
    Report = RunCalibration(ManifestPath, OutputPath)
    assert (
        Report["completed_sweep"] is True
        and Report["native_acceptance"] == "not_established"
    )
    assert Report["recommended_concurrency"] is None
    assert Report["requested_steps"] == [1, 2, 4, 8]
    assert Report["adaptive_limits"] is False and Report["grouping"] is False
    Inodes: set[int] = set()
    for Requested in (1, 2, 4, 8):
        TrialPath = OutputPath / f"Trial{Requested}"
        CheckTrial(TrialPath, Requested, TmpPath / "Input.f3d")
        Trial = JsonCodec.loads((TrialPath / "Trial.json").read_text(encoding="utf-8"))
        assert Trial["requested_concurrency"] == Requested
        assert Trial["execution_completed"] is True and Trial["completed_jobs"] == 8
        assert Trial["observed_peak_decode_concurrency"] <= 1
        assert Trial["physical_process_cpu_seconds_observed"] > 0
        assert (
            Trial["cpu_measurements_complete"] is True
            and Trial["rss_measurements_complete"] is True
        )
        assert Trial["peak_worker_or_group_rss_bytes"] > 0
        assert Trial["wall_seconds"] > 0
        assert Trial["source_identity"]["registry_sha256"]
        if Requested > 1:
            assert Trial["complete"] is False
            assert "resource_capacity:offline:slot" in Trial["incomplete_reasons"]
        Inodes.add((TrialPath / "Controller" / "ledger.sqlite3").stat().st_ino)
    assert len(Inodes) == 4
    assert not any(
        Entry["comparable"]
        for Entry in CastValue(list[dict[str, object]], Report["comparisons"])
    )


# real archive compatibility requires accepted member results in the grouped arm and identical singleton outputs
def CheckGrouped(TmpPath: FilePath) -> None:
    ManifestPath = BuildManifest(TmpPath, MaxSeconds=60)
    Manifest = JsonCodec.loads(ManifestPath.read_text(encoding="utf-8"))
    Manifest["resources"]["offline:slot"]["capacity"] = 20
    for Member in Manifest["jobs"]:
        Member["lease_seconds"] = 30
        Member["timeout_seconds"] = 60
    _ = ManifestPath.write_text(JsonCodec.dumps(Manifest), encoding="utf-8")
    Report = JsonCodec.loads(
        JsonCodec.dumps(
            RunCalibration(
                ManifestPath, TmpPath / "Paired", ExitCode=None, CompareGrouped=True
            )
        )
    )
    assert Report["scope"] == "paired-single-slot-grouped-offline"
    Singleton, Grouped = Report["trials"]
    for ArmInfo in (Singleton, Grouped):
        assert ArmInfo["execution_completed"] and ArmInfo["completed_jobs"] == 8
        assert ArmInfo["group_receipts_verified"] is True
        assert ArmInfo["cpu_measurements"] == ArmInfo["physical_sessions"]
    assert Singleton["physical_sessions"] == 8
    assert Singleton["multi_member_sessions"] == 0
    assert 1 <= Grouped["physical_sessions"] < 8
    assert Grouped["multi_member_sessions"] >= 1
    assert Singleton["decoded_outputs_sha256"] == Grouped["decoded_outputs_sha256"]
    (Comparison,) = Report["comparisons"]
    assert Report["completed_sweep"] is Comparison["comparable"]
    if not Comparison["comparable"]:
        assert Report["stop_reason"] == Comparison["reason"] == "paired_arm_incomplete"
