import hashlib as Hashlib
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest

from convert.api.ApiOpen import OpenDocument
from interchange.geometry.models.GeometryCurves import PointGeometry


# each command compares saved archive records with pinned independent application measurements
@Pytest.mark.parametrize(
    ("ScriptPath", "Options", "ReportDigest"),
    (
        Pytest.param(
            "re/solidworks/archive/RectangularPlaneEvidence.py",
            ("--through-operation", "--include-coincidence"),
            "33c94376c4e892b93cf7046f62a6ea0a25d32876f147fd49bf5b217e1edb82a4",
            id="solidworks-p01-p03-resolved-list",
        ),
        Pytest.param(
            "re/solidworks/archive/ResolvedEntry.py",
            ("--through-operation",),
            "9ecde927c05c451e4f703eaf101748d75165d0a80d5f6db5f12a3615a328f257",
            id="solidworks-p04-resolved-list",
        ),
        Pytest.param(
            "re/solidworks/archive/SketchEvidence.py",
            ("--include-coincidence",),
            "d339efac5b24a262f50fe343d778349627d628cf9d09aa080c12461245bd3677",
            id="solidworks-p04-sketch-operands",
        ),
        Pytest.param(
            "re/automation/FusionRectangleSketchEvidence.py",
            (),
            "aa4ec3c20c2a977d123853c17e7b48acb26743ef10252a1a34af0d43d16b8d13",
            id="fusion-p01-rectangle-operands",
        ),
        Pytest.param(
            "re/automation/FusionBossProfileEvidence.py",
            (),
            "567c2c0993e27d197d394bd504545a4efadce6b6d1dd221cf2b35b828ce58e77",
            id="fusion-p03-boss-profile",
        ),
        Pytest.param(
            "re/automation/FusionCutProfileEvidence.py",
            (),
            "4ac34b4dbb4b92473aab572336e0ef6402634b0c534f9c6a502b81cc9575b75c",
            id="fusion-p04-cut-profile",
        ),
        Pytest.param(
            "re/automation/FusionCutProjectionEvidence.py",
            (),
            "d8082c5685313c1634ebdbb6c5b52bbec51f6216e056f6175c473d811e4a86f4",
            id="fusion-p04-projected-edges",
        ),
        Pytest.param(
            "re/automation/FusionCutCenterEvidence.py",
            (),
            "4710c3797a353177650acff289019173ad1d3a450d8eff49c54872aa6e5c6256",
            id="fusion-p04-cut-center",
        ),
        Pytest.param(
            "re/automation/FusionP04RelationEvidence.py",
            (),
            "8a5ea4dfb4ee3e6dcd8b38e13a5b2049693bb799c50e955e49983aa64a7649d3",
            id="fusion-p04-sketch-relations",
        ),
    ),
)
def CheckArchive(ScriptPath: str, Options: tuple[str, ...], ReportDigest: str) -> None:
    RepoPath = FilePath(__file__).resolve().parents[2]
    ResultInfo = Subprocess.run(
        [System.executable, "-B", ScriptPath, *Options],
        cwd=RepoPath,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr.decode(errors="replace")
    ActualDigest = Hashlib.sha256(ResultInfo.stdout.replace(b"\r\n", b"\n")).hexdigest()
    assert ActualDigest == ReportDigest, (ScriptPath, Options, ActualDigest)


# the feature selected profile must carry the exact proxy and authored perimeter across the registry
@Pytest.mark.parametrize(
    ("Family", "Capture", "Variant", "FeatureId", "ProxyId", "DescriptorId", "Edges"),
    (
        (
            "P03",
            "8d53584027ff",
            "direction-negative",
            "277",
            278,
            281,
            (232, 238, 244, 248),
        ),
        ("P04", "9cf53a55ea8b", "baseline-a", "446", 454, 457, (393, 396, 399, 400)),
        ("P04", "9cf53a55ea8b", "plane-yz", "446", 454, 457, (393, 396, 399, 400)),
        (
            "P04",
            "9cf53a55ea8b",
            "termination-through-all",
            "446",
            454,
            457,
            (393, 396, 399, 400),
        ),
    ),
)
def CheckOwnedPick(
    Family: str,
    Capture: str,
    Variant: str,
    FeatureId: str,
    ProxyId: int,
    DescriptorId: int,
    Edges: tuple[int, ...],
) -> None:
    RootDir = FilePath(__file__).resolve().parents[2]
    Archive = (
        RootDir
        / f"re/automation/PairedCaptures/{Family}/fusion-{Capture}"
        / f"{Family}-fusion-{Variant}.f3d"
    )
    Document = OpenDocument(Archive, StrictMode=False)
    (Feature,) = [
        Value
        for Value in Document.feature_timeline
        if Value.provenance is not None and Value.provenance.native_id == FeatureId
    ]
    assert Feature.attributes["fusion.profile_selection_proxy_id"] == ProxyId
    assert Feature.attributes["fusion.profile_descriptor_id"] == DescriptorId
    assert Feature.provenance is not None
    assert any(
        Evidence.record_kind == "2CA5A1CD-C99B-4C9B-91AF-57989148E841"
        for Evidence in Feature.provenance.spans
    )
    (Sketch,) = [Value for Value in Document.sketches if Value.id == Feature.sketch_id]
    (Perimeter,) = Sketch.closed_profile_entity_ids
    assert set(Perimeter) == {f"fusion-sketch-entity-{Identity}" for Identity in Edges}


# native support identity must survive public discovery without substituting a sketch basis
@Pytest.mark.parametrize(
    ("Family", "Capture", "Variant", "Datum", "DatumId", "AxisX"),
    (
        ("P01", "5dc3245eb59c", "baseline-a", "XY", 42, (1.0, 0.0, 0.0)),
        ("P01", "5dc3245eb59c", "plane-yz", "YZ", 44, (0.0, 0.0, -1.0)),
        ("P03", "8d53584027ff", "baseline-a", "XY", 42, (1.0, 0.0, 0.0)),
        ("P03", "8d53584027ff", "plane-yz", "YZ", 44, (0.0, 0.0, -1.0)),
    ),
)
def CheckDatum(
    Family: str,
    Capture: str,
    Variant: str,
    Datum: str,
    DatumId: int,
    AxisX: tuple[float, float, float],
) -> None:
    RootDir = FilePath(__file__).resolve().parents[2]
    Archive = (
        RootDir
        / f"re/automation/PairedCaptures/{Family}/fusion-{Capture}"
        / f"{Family}-fusion-{Variant}.f3d"
    )
    Document = OpenDocument(Archive, StrictMode=False)
    (Sketch,) = [
        Value for Value in Document.sketches if Value.name == "RectangleSketch"
    ]
    (Plane,) = [
        Value
        for Value in Document.support_planes
        if Value.id == Sketch.support_plane_id
    ]
    assert Plane.attributes["fusion.native_support_resolved"] is True
    assert Plane.attributes["fusion.native_support_name"] == Datum
    assert Plane.attributes["fusion.native_support_object_id"] == DatumId
    assert (
        Plane.transform.x_axis.x,
        Plane.transform.x_axis.y,
        Plane.transform.x_axis.z,
    ) == AxisX
    assert Plane.provenance is not None
    assert any(
        Evidence.record_kind == "8D424E29-DE23-4B1F-A3AD-84C52A497D1A"
        for Evidence in Plane.provenance.spans
    )
    assert "fusion.native_state" not in Document.metadata


# the saved boss cap would misleadingly look like an origin plane without its selection records
def CheckFaceDatum() -> None:
    RootDir = FilePath(__file__).resolve().parents[2]
    Archive = (
        RootDir
        / "re/automation/PairedCaptures/P04/fusion-9cf53a55ea8b"
        / "P04-fusion-baseline-a.f3d"
    )
    Document = OpenDocument(Archive, StrictMode=False)
    (Sketch,) = [Value for Value in Document.sketches if Value.name == "CutSketch"]
    (Plane,) = [
        Value
        for Value in Document.support_planes
        if Value.id == Sketch.support_plane_id
    ]
    assert Plane.attributes["fusion.native_support_resolved"] is False
    assert "fusion.native_support_object_id" not in Plane.attributes


# dependent dimensions must keep saved argument and dependency orders across the public reading boundary
@Pytest.mark.parametrize(
    "Variant",
    (
        "baseline-a",
        "baseline-b",
        "edit-width_mm-44",
        "edit-height_mm-24",
        "edit-depth_mm-12",
        "edit-cut_width_mm-12",
        "edit-cut_height_mm-10",
        "edit-cut_depth_mm-5",
        "units-inch",
        "plane-yz",
        "termination-through-all",
    ),
)
def CheckDimOrder(Variant: str) -> None:
    RootDir = FilePath(__file__).resolve().parents[2]
    Archive = (
        RootDir
        / "re/automation/PairedCaptures/P04/fusion-9cf53a55ea8b"
        / f"P04-fusion-{Variant}.f3d"
    )
    Document = OpenDocument(Archive, StrictMode=False)
    Parameters = {Value.id: Value.name for Value in Document.parameters}
    Dimensions = {
        Parameters[Value.parameter_id]: Value
        for Sketch in Document.sketches
        for Value in Sketch.constraints
        if Value.parameter_id is not None
    }
    Expected = {
        "width_mm": ((228, 230), (228, 230), (1, 0), 1),
        "height_mm": ((242, 228), (228, 242), (2, 0), -1),
        "cut_width_mm": ((389, 391), (389, 391), (0, 0), 1),
        "cut_height_mm": ((397, 389), (389, 397), (1, 0), -1),
        "cut_center_u_mm": ((428, 406), (406, 428), (1, 0), 1),
        "cut_center_v_mm": ((428, 406), (406, 428), (2, 1), 1),
    }
    assert set(Dimensions) == set(Expected)
    for NameValue, (Operands, Dependencies, Slots, AxisSign) in Expected.items():
        Dimension = Dimensions[NameValue]
        Attrs = Dimension.attributes
        assert tuple(Value.entity_id for Value in Dimension.references) == tuple(
            f"fusion-sketch-entity-{Identity}" for Identity in Operands
        )
        assert tuple(Value.point for Value in Dimension.references) == (
            "start",
            "start",
        )
        assert Dimension.driving
        if Slots != (0, 0):
            assert Attrs["fusion.dimension_dependency_object_ids"] == Dependencies
            assert Attrs["fusion.dimension_dependency_slots"] == Slots
        else:
            assert "fusion.dimension_dependency_slots" not in Attrs
        if Variant == "plane-yz" and NameValue in (
            "height_mm",
            "cut_height_mm",
            "cut_center_v_mm",
        ):
            AxisSign = -AxisSign
        assert Attrs["fusion.signed_distance_multiplier"] == AxisSign


# the saved corner anchor must survive the public registry with both distinct native identities
@Pytest.mark.parametrize(
    ("Family", "Capture", "Variant"),
    (
        ("P01", "5dc3245eb59c", "baseline-a"),
        ("P03", "8d53584027ff", "plane-yz"),
        ("P04", "9cf53a55ea8b", "termination-through-all"),
    ),
)
def CheckCoincident(Family: str, Capture: str, Variant: str) -> None:
    RootDir = FilePath(__file__).resolve().parents[2]
    Archive = (
        RootDir
        / f"re/automation/PairedCaptures/{Family}/fusion-{Capture}"
        / f"{Family}-fusion-{Variant}.f3d"
    )
    Document = OpenDocument(Archive, StrictMode=False)
    (Sketch,) = [
        Value for Value in Document.sketches if Value.name == "RectangleSketch"
    ]
    (Relation,) = [Value for Value in Sketch.constraints if Value.kind == "coincident"]
    assert tuple(Value.entity_id for Value in Relation.references) == (
        "fusion-sketch-entity-228",
        "fusion-sketch-entity-205",
    )
    assert Relation.attributes["fusion.constraint_argument_ids"] == (228, 205)
    assert Relation.attributes["fusion.constraint_dependency_ids"] == (205, 228)
    Entities = {Entity.id: Entity for Entity in Sketch.entities}
    for Target in Relation.references:
        Geometry = Entities[Target.entity_id].geometry
        assert isinstance(Geometry, PointGeometry)
        assert (Geometry.point.x, Geometry.point.y) == (0.0, 0.0)
