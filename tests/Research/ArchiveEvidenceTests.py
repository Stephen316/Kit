import hashlib as Hashlib
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath
from struct import unpack_from as UnpackFrom

import pytest as Pytest

from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.api.ApiOpen import OpenDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import PointGeometry
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.VectorSpace import SpaceVector


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


# public support must use the saved reference even when the front plane occurs first
@Pytest.mark.parametrize(
    ("Family", "Capture", "Variant"),
    (
        ("P01", "75b9308cf13e", "baseline-a"),
        ("P01", "75b9308cf13e", "baseline-b"),
        ("P01", "75b9308cf13e", "edit-height_mm-23"),
        ("P01", "75b9308cf13e", "edit-width_mm-41"),
        ("P01", "75b9308cf13e", "plane-yz"),
        ("P01", "75b9308cf13e", "units-inch"),
        ("P03", "db1390476325", "baseline-a"),
        ("P03", "db1390476325", "baseline-b"),
        ("P03", "db1390476325", "direction-negative"),
        ("P03", "db1390476325", "edit-depth_mm-12"),
        ("P03", "db1390476325", "edit-height_mm-23"),
        ("P03", "db1390476325", "edit-width_mm-41"),
        ("P03", "db1390476325", "plane-yz"),
        ("P03", "db1390476325", "units-inch"),
    ),
)
def CheckSwSupport(Family: str, Capture: str, Variant: str) -> None:
    RootDir = FilePath(__file__).resolve().parents[2]
    NativePath = (
        RootDir
        / "re/automation/PairedCaptures"
        / Family
        / f"solidworks-{Capture}"
        / f"{Family}-solidworks-{Variant}.SLDPRT"
    )
    Document = OpenDocument(NativePath)
    (Sketch,) = tuple(
        Value
        for Value in Document.sketches
        if Value.attributes.get("support_plane_source") == "typed-archive-reference"
    )
    (Frame,) = tuple(
        Value
        for Value in Document.support_planes
        if Value.id == Sketch.support_plane_id
    )
    DatumId = 4 if Variant == "plane-yz" else 2
    Normal = (1, 0, 0) if DatumId == 4 else (0, 0, 1)
    AxisX = (0, 0, -1) if DatumId == 4 else (1, 0, 0)
    assert Frame.name == ("Right Plane" if DatumId == 4 else "Front Plane")
    assert Sketch.attributes["support_plane_native_id"] == DatumId
    assert Frame.transform.origin == SpaceVector(0, 0, 0)
    assert Frame.transform.z_axis == SpaceVector(*Normal)
    assert Frame.transform.x_axis == SpaceVector(*AxisX)
    assert Sketch.provenance is not None
    (SupportSpan,) = tuple(
        Value
        for Value in Sketch.provenance.spans
        if Value.record_kind == "sketch-support-reference"
    )
    assert (
        SupportSpan.stream == "Contents/Config-0-ResolvedFeatures"
        and SupportSpan.length == 4
    )
    Archive = SldprtArchive.from_bytes(NativePath.read_bytes())
    Stored = Archive.require(SupportSpan.stream)[
        SupportSpan.offset : SupportSpan.offset + SupportSpan.length
    ]
    assert int.from_bytes(Stored, "little", signed=True) == DatumId


# native depth and signed direction must survive display-unit changes and the public projection
@Pytest.mark.parametrize(
    "Variant",
    (
        "baseline-a",
        "baseline-b",
        "direction-negative",
        "edit-depth_mm-12",
        "edit-height_mm-23",
        "edit-width_mm-41",
        "plane-yz",
        "units-inch",
    ),
)
def CheckSwBoss(Variant: str) -> None:
    NativePath = (
        FilePath(__file__).resolve().parents[2]
        / "re/automation/PairedCaptures/P03/solidworks-db1390476325"
        / f"P03-solidworks-{Variant}.SLDPRT"
    )
    Document = OpenDocument(NativePath)
    (Boss,) = tuple(
        Item for Item in Document.feature_timeline if Item.name == "BlindBoss"
    )
    Definition = Boss.definition
    assert isinstance(Definition, ExtrudeFeature)
    Depth = 12 if Variant == "edit-depth_mm-12" else 10
    assert Definition.length is not None
    assert (Definition.length.value, Definition.length.unit) == (Depth, "mm")
    assert Definition.end_condition == ExtrudeEnd.BLIND
    assert Definition.reversed == (Variant == "direction-negative")
    (SketchValue,) = tuple(
        Item for Item in Document.sketches if Item.id == Boss.sketch_id
    )
    assert SketchValue.name == "RectangleSketch"
    assert Boss.provenance is not None
    Spans = {Span.record_kind: Span for Span in Boss.provenance.spans}
    assert Spans["operation-profile-reference"].length == 2
    assert Spans["extrusion-end-spec"].length > 20
    Scalar = Spans["extrusion-depth-scalar"]
    assert Scalar.stream == "Contents/Config-0-ResolvedFeatures" and Scalar.length == 8
    Archive = SldprtArchive.from_bytes(NativePath.read_bytes())
    assert UnpackFrom("<d", Archive.require(Scalar.stream), Scalar.offset) == (
        Depth / 1000,
    )
    (Parameter,) = tuple(
        Item for Item in Document.parameters if Item.id in Boss.parameter_ids
    )
    assert (Parameter.name, Parameter.value.value, Parameter.value.unit) == (
        "depth_mm",
        Depth,
        "mm",
    )
    assert Parameter.provenance is not None
    assert [(Span.offset, Span.length) for Span in Parameter.provenance.spans] == [
        (Scalar.offset, 8)
    ]


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
    assert Plane.attributes["fusion.native_support_resolved"] is True
    assert "fusion.native_support_object_id" not in Plane.attributes
    assert (
        Plane.attributes["fusion.native_support_kind"] == "historical_face_occurrence"
    )


# both public checks must exercise the same saved cut discovery roster
KCutVariants = (
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
)

# saved edge allocations vary across edits so each archive supplies its own expected source start
KSupportEdgeStarts = {
    "baseline-a": 504,
    "baseline-b": 552,
    "edit-width_mm-44": 627,
    "edit-height_mm-24": 777,
    "edit-depth_mm-12": 924,
    "edit-cut_width_mm-12": 1043,
    "edit-cut_height_mm-10": 1137,
    "edit-cut_depth_mm-5": 1229,
    "units-inch": 1318,
    "plane-yz": 504,
    "termination-through-all": 512,
}


# cut archive checks share the normal adapter boundary and exact source location
def OpenCutArchive(Variant: str) -> CadDocument:
    RootDir = FilePath(__file__).resolve().parents[2]
    Archive = (
        RootDir
        / "re/automation/PairedCaptures/P04/fusion-9cf53a55ea8b"
        / f"P04-fusion-{Variant}.f3d"
    )
    return OpenDocument(Archive, StrictMode=False)


# source coordinates must vary with the saved chart while the historical body remains scoped
def AssertBodyChart(Variant: str, Support: Selection) -> None:
    Attributes = Support.attributes
    Expected = {
        "plane-yz": (5, 196, 25480),
        "termination-through-all": (5, 194, 25160),
    }
    Handle, Ordinal, Start = Expected.get(
        Variant, (KCutVariants.index(Variant) + 5, 195, 25311)
    )
    assert "fusion.history_body_unresolved" not in Attributes, Attributes
    assert Attributes["fusion.history_body_handle"] == Handle
    assert Attributes["fusion.history_body_source_ordinal"] == Ordinal
    assert Attributes["fusion.history_body_result_ordinal"] == 1
    SourceClock = Attributes["fusion.history_body_source_clock"]
    ResultClock = Attributes["fusion.history_body_result_clock"]
    assert type(SourceClock) is int and type(ResultClock) is int
    assert 0 < SourceClock < ResultClock < (1 << 53)
    Member = Attributes["fusion.history_body_member"]
    assert isinstance(Member, str) and Member.endswith(".smbh")
    Digest = Attributes["fusion.history_body_sha256"]
    assert isinstance(Digest, str) and len(Digest) == 64
    assert Support.provenance is not None
    assert [
        (Origin.offset, Origin.length, Origin.record_kind)
        for Origin in Support.provenance.spans
        if Origin.stream == Member and Origin.record_kind == "body"
    ] == [(186, 61, "body"), (Start, 61, "body")]


# native ring ordinals must report original stored occurrences outside the view namespace
def AssertFaceChart(Variant: str, Support: Selection) -> None:
    Expected = {
        "plane-yz": (
            194,
            25319,
            68,
            96,
            (113, 131, 156, 133),
            (137, 138, 159, 161),
        ),
        "termination-through-all": (
            190,
            24716,
            114,
            142,
            (167, 180, 173, 158),
            (160, 181, 174, 162),
        ),
    }
    FaceId, Start, LoopId, PlaneId, Edges, Vertices = Expected.get(
        Variant, (193, 25150, 67, 95, (112, 130, 155, 132), (136, 137, 158, 160))
    )
    Attributes = Support.attributes
    assert "fusion.history_face_unresolved" not in Attributes, Attributes
    assert Attributes["fusion.history_face_ordinal"] == FaceId
    assert Attributes["fusion.history_face_loop_ordinal"] == LoopId
    assert Attributes["fusion.history_face_surface_ordinal"] == PlaneId
    assert Attributes["fusion.history_face_edge_ordinals"] == Edges
    assert Attributes["fusion.history_face_vertex_ordinals"] == Vertices
    assert Support.provenance is not None
    assert [
        (Origin.offset, Origin.length)
        for Origin in Support.provenance.spans
        if Origin.stream == Attributes["fusion.history_body_member"]
        and Origin.record_kind == "face"
    ] == [(Start, 81)]


# edits and rotated support preserve exact sources for the four cached reference lines
def AssertCapRim(Variant: str, SketchValue: Sketch, Support: Selection) -> None:
    Expected = {
        "plane-yz": ((113, 131, 156, 133), (137, 138, 159, 161)),
        "termination-through-all": ((167, 180, 173, 158), (160, 181, 174, 162)),
    }
    Edges, Vertices = Expected.get(
        Variant, ((112, 130, 155, 132), (136, 137, 158, 160))
    )
    Lines = {
        Value.id: Value
        for Value in SketchValue.entities
        if Value.attributes.get("fusion.projection_mode") == "automatic_face_boundary"
    }
    assert set(Lines) == {
        f"fusion-sketch-entity-{Identity}" for Identity in (381, 384, 387, 388)
    }
    for Identity, EdgeId, Start, Finish in zip(
        (381, 384, 387, 388), Edges, Vertices, Vertices[1:] + Vertices[:1], strict=True
    ):
        LineValue = Lines[f"fusion-sketch-entity-{Identity}"]
        assert LineValue.attributes["fusion.projection_source_edge_ordinal"] == EdgeId
        assert LineValue.attributes["fusion.projection_source_vertex_ordinals"] == (
            Start,
            Finish,
        )
        assert LineValue.attributes["fusion.projection_controller_object_id"] == 346
        Member = Support.attributes["fusion.history_body_member"]
        assert LineValue.attributes["fusion.projection_source_member"] == Member
        assert LineValue.provenance is not None
        assert [
            Value.record_kind
            for Value in LineValue.provenance.spans
            if Value.stream == Member
        ] == ["edge", "vertex", "vertex"]


# the feature must preserve its historical target without adding the extent selector
@Pytest.mark.parametrize("Variant", KCutVariants)
def CheckCutTarget(Variant: str) -> None:
    Document = OpenCutArchive(Variant)
    Features = {
        Value.provenance.native_id: Value
        for Value in Document.feature_timeline
        if Value.provenance is not None
    }
    Cutter, Source = Features["446"], Features["277"]
    (Target,) = [
        Value
        for Value in Document.selections
        if Value.id in Cutter.selection_ids and Value.query.get("role") == "target"
    ]
    assert Cutter.operation == "cut"
    assert Target.id not in Source.selection_ids
    assert Target.path == ()
    assert Target.query["kind"] == "historical_body"
    assert Target.query["role"] == "target"
    assert Target.query["native_body_id"] == 309
    assert Target.query["native_anchor_id"] == 315
    assert Target.query["native_source_id"] == 277
    assert Target.query["source_feature_id"] == Source.id
    assert Target.query["native_component_id"] == 3
    assert Target.query["native_scope_id"] == 33
    assert Target.query["native_history_id"] == 35
    assert Target.attributes["fusion.proxy_object_id"] == 447
    assert Target.attributes["fusion.descriptor_object_id"] == 450
    assert Target.attributes["fusion.support_object_id"] == 451
    assert Target.attributes["fusion.recipe_object_id"] == 453
    assert Target.attributes["fusion.context_object_ids"] == ()
    AssertCutEnding(Variant, Cutter, Document)


# through all must retain its authored selector without synthesizing a dimension
def AssertCutAll(
    Cutter: FeatureStep, Definition: ExtrudeFeature, Document: CadDocument
) -> None:
    assert Definition.end_condition == ExtrudeEnd.KThroughAll
    assert Definition.length is None
    assert Definition.up_to_reference == ""
    assert Cutter.attributes["fusion.extrude.end_flags"] == 2
    assert "fusion.extrude.along_parameter_id" not in Cutter.attributes
    (Extent,) = [
        Value
        for Value in Document.selections
        if Value.id in Cutter.selection_ids
        and Value.query.get("role") == "extent_reference"
    ]
    assert Cutter.attributes["fusion.extrude.end_selector_id"] == Extent.id
    assert Extent.query["native_body_id"] == 309
    assert Extent.query["native_anchor_id"] == 315
    assert Extent.query["native_source_id"] == 277
    assert Extent.attributes["fusion.proxy_object_id"] == 461
    assert Extent.attributes["fusion.descriptor_object_id"] == 464
    assert Extent.attributes["fusion.context_object_ids"] == (536,)


# the edited value and the rotated basis distinguish genuine saved direction and depth
def AssertCutEnding(Variant: str, Cutter: FeatureStep, Document: CadDocument) -> None:
    Definition = Cutter.definition
    assert isinstance(Definition, ExtrudeFeature), Document.diagnostics
    assert Definition.direction == (
        SpaceVector(-1.0, 0.0, 0.0)
        if Variant == "plane-yz"
        else SpaceVector(0.0, 0.0, -1.0)
    )
    if Variant == "termination-through-all":
        AssertCutAll(Cutter, Definition, Document)
        return
    assert Definition.end_condition == ExtrudeEnd.KBlind
    assert Cutter.attributes["fusion.extrude.end_flags"] == 0
    assert "fusion.extrude.end_selector_id" not in Cutter.attributes
    assert Definition.length is not None
    Depth = 0.5 if Variant == "edit-cut_depth_mm-5" else 0.4
    assert Definition.length.unit == "cm"
    assert Definition.length.value == Depth
    (Owned,) = [
        Value
        for Value in Document.parameters
        if Value.id == Cutter.attributes["fusion.extrude.along_parameter_id"]
    ]
    assert Owned.id in Cutter.parameter_ids
    assert Owned.owner_id == Cutter.id
    assert Owned.value.value == -Depth
    assert Owned.expression is not None
    assert Owned.expression.source == f"-( {int(10 * Depth)} mm )"


# a coincident cached frame must still carry the separately authored face recipe instead of a datum
@Pytest.mark.parametrize("Variant", KCutVariants)
def CheckCutSupport(Variant: str) -> None:
    Document = OpenCutArchive(Variant)
    (Sketch,) = [Value for Value in Document.sketches if Value.name == "CutSketch"]
    (Plane,) = [
        Value
        for Value in Document.support_planes
        if Value.id == Sketch.support_plane_id
    ]
    (Support,) = [
        Value for Value in Document.selections if Value.id == Plane.support_selection_id
    ]
    assert Plane.attributes["fusion.native_support_resolved"] is True
    assert "fusion.native_support_object_id" not in Plane.attributes
    assert (
        Plane.attributes["fusion.native_support_kind"] == "historical_face_occurrence"
    )
    assert Support.path == ()
    assert Support.query["kind"] == "historical_face_recipe"
    assert Support.query["role"] == "sketch_support"
    assert Support.query["native_body_id"] == 309
    assert Support.query["native_anchor_id"] == 315
    assert Support.query["native_source_id"] == 277
    assert Support.query["native_face_name"] == "2"
    assert Support.attributes["fusion.proxy_object_id"] == 347
    assert Support.attributes["fusion.descriptor_object_id"] == 350
    assert Support.attributes["fusion.recipe_object_id"] == 353
    FirstEdge = KSupportEdgeStarts[Variant]
    assert Support.attributes["fusion.edge_recipe_object_ids"] == tuple(
        range(FirstEdge, FirstEdge + 16, 4)
    )
    AssertBodyChart(Variant, Support)
    AssertFaceChart(Variant, Support)
    AssertCapRim(Variant, Sketch, Support)
    assert "fusion.native_state" not in Document.metadata


# dependent dimensions must keep saved argument and dependency orders across the public reading boundary
@Pytest.mark.parametrize("Variant", KCutVariants)
def CheckDimOrder(Variant: str) -> None:
    Document = OpenCutArchive(Variant)
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
    AssertCenters(Document)


# the center link must follow the authored origin and exact earlier named dimension
def AssertCenters(Document: CadDocument) -> None:
    Params = {Value.name: Value for Value in Document.parameters}
    (Sketch,) = [Value for Value in Document.sketches if Value.name == "CutSketch"]
    (Origin,) = [
        Value
        for Value in Sketch.entities
        if Value.attributes.get("fusion.projection_mode") == "origin_project"
    ]
    assert Origin.id == "fusion-sketch-entity-428"
    assert Origin.attributes["fusion.projection_source_object_id"] == 38
    assert Origin.provenance is not None
    assert any(
        Evidence.record_kind == "F1451EC8-11A4-4952-84ED-5AB7C13E2E83"
        for Evidence in Origin.provenance.spans
    )
    for NameValue, DriverName in (
        ("cut_center_u_mm", "width_mm"),
        ("cut_center_v_mm", "height_mm"),
    ):
        Center = Params[NameValue]
        assert Center.expression is not None
        assert Center.expression.source == f"{DriverName} / 2"
        assert Center.expression.parameter_ids == (
            Params[DriverName].id,
        ), Document.diagnostics
        assert (
            Center.attributes["fusion.expression_binding"]
            == "scoped_dimension_registry"
        )


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
