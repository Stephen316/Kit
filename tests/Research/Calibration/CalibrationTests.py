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
