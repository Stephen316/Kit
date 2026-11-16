import json as JsonData
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath
from typing import cast as CastValue

import pytest as Pytest

from tests.Research.Archives.ArchiveEvidenceTests import KCutVariants


# the hosted process boundary supplies plain json objects
def ReportObject(Value: object) -> dict[str, object]:
    assert isinstance(Value, dict)
    return CastValue(dict[str, object], Value)


# matching body measurements and profiles still allow different authored positioning
def AssertCutPairs(Pairs: dict[str, object]) -> None:
    assert set(Pairs) == set(KCutVariants)
    for Variant, Value in Pairs.items():
        PairValue = ReportObject(Value)
        BodyValue = ReportObject(PairValue["body"])
        assert BodyValue["status"] == "equal", (Variant, BodyValue)
        Comparisons = ReportObject(BodyValue["comparisons"])
        assert set(Comparisons) == {
            "between_readers",
            "fusion_to_historical",
            "solidworks_to_original_reopen",
        }
        History = ReportObject(PairValue["history"])
        Profiles = ReportObject(History["profiles"])
        assert ReportObject(Profiles["base"])["status"] == "equal", (Variant, Profiles)
        assert ReportObject(Profiles["cut"])["status"] == "equal", (Variant, Profiles)
        Positioning = ReportObject(Profiles["cut_positioning"])
        assert Positioning["status"] == "meaningfully_different", (Variant, Positioning)
        assert ReportObject(History["cut_support_plane"])["status"] == "equal", Variant
        Extent = ReportObject(History["cut_extent"])
        assert Extent["status"] == "equal", (Variant, Extent)
        AssertCutAxes(History, Variant)


# the verified cap direction is inward even when both applications report the same depth
def AssertCutAxes(History: dict[str, object], Variant: str) -> None:
    BaseAxis = [1.0, 0.0, 0.0] if Variant == "plane-yz" else [0.0, 0.0, 1.0]
    CutAxis = [-Component for Component in BaseAxis]
    for Field, AxisValue in (("base_direction", BaseAxis), ("cut_direction", CutAxis)):
        Direction = ReportObject(History[Field])
        assert Direction["status"] == "equal", (Variant, Direction)
        assert Direction["fusion"] == Direction["solidworks"] == AxisValue
    Issues = History["unclassified"]
    assert isinstance(Issues, list)
    assert "SOLIDWORKS persisted through-all body-selection policy" in Issues


# the duplicate boundary control preserves both identities without selecting one
def AssertCutLinks(Report: dict[str, object]) -> None:
    Ambiguous = ReportObject(Report["ambiguous_boundary_control"])
    assert Ambiguous["status"] == "ambiguous", Ambiguous
    assert "matched_links" not in Ambiguous
    Links = Ambiguous["candidate_links"]
    assert isinstance(Links, list)
    Candidates = [ReportObject(Entry) for Entry in CastValue(list[object], Links)]
    Copied = next(
        Entry
        for Entry in Candidates
        if Entry["second_id"] == "duplicated_geometry_control"
    )
    SourceId = Copied["first_id"]
    Alternatives = [Entry for Entry in Candidates if Entry["first_id"] == SourceId]
    assert [
        (Entry["second_id"], Entry["maximum_endpoint_delta_mm"])
        for Entry in Alternatives
    ] == [(SourceId, 0.0), ("duplicated_geometry_control", 0.0)]


# the actual through all control changes solid geometry despite identical axis bounds
def AssertCutDiff(Report: dict[str, object]) -> None:
    Controls = ReportObject(Report["termination_difference_control"])
    Change = ReportObject(Controls["public_baseline_solidworks_vs_through_all_fusion"])
    assert Change["status"] == "different" and Change["counts_exact"] is False
    assert Change["maximum_bound_difference_mm"] == Pytest.approx(0.0, abs=1e-6)
    assert Change["volume_difference_mm3"] == Pytest.approx(480.0, abs=1e-6, rel=0.0)
    assert "historical_baseline_solidworks_vs_through_all_fusion" not in Controls
    Extents = Controls["baseline_and_through_all_cut_extents"]
    assert Extents == [
        {"status": "equal", "fusion": ["blind", 4.0], "solidworks": ["blind", 4.0]},
        {
            "status": "equal",
            "fusion": ["through_all", None],
            "solidworks": ["through_all", None],
        },
    ]


# hosted discovery reads the repository receipts and public adapter without a licensed host
def CheckCutHistory() -> None:
    RepoPath = FilePath(__file__).resolve().parents[3]
    Result = Subprocess.run(
        [System.executable, "-B", "re/automation/CutHistoryEvidence.py", "--git-only"],
        cwd=RepoPath,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr.decode(errors="replace")
    Report = ReportObject(JsonData.loads(Result.stdout))
    assert "historical_body_evidence" not in Report
    assert Report["fresh_native_fusion"] == "unverified"
    AssertCutPairs(ReportObject(Report["pairs"]))
    AssertCutLinks(Report)
    AssertCutDiff(Report)
