import hashlib as Hashlib
import subprocess as Subprocess
import sys as System
from math import hypot as Hypot
from pathlib import Path as FilePath
from struct import unpack_from as UnpackFrom

import pytest as Pytest

from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.api.ApiOpen import OpenDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch, SketchRelation
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import Parameter
from tests.Research.Archives.SwPlanarLoops import VerifySwExport, VerifySwLoops


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
            "re/solidworks/archive/ConfigMap.py",
            (),
            "d54ce30559d5905d56c290f4dabb3e961861673afeccc3071dc7cac40202853a",
            id="solidworks-p04-configuration-map",
        ),
        Pytest.param(
            "re/solidworks/archive/ResolvedEntry.py",
            ("--through-operation",),
            "9ecde927c05c451e4f703eaf101748d75165d0a80d5f6db5f12a3615a328f257",
            id="solidworks-p04-resolved-list",
        ),
        Pytest.param(
            "re/solidworks/archive/FaceEvidence.py",
            (),
            "2005a0fb4ea376c4d55ae499a796e239351b6b0ff743f04656f687c41c1a0a98",
            id="solidworks-p04-face-support-witness",
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
            "re/automation/RectanglePairEvidence.py",
            (),
            "8eb38234c8a909d43bfee6730fdfd672f1ac8787d3b90c51009b70bb19660afc",
            id="paired-p01-p03-public-history",
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
    RepoPath = FilePath(__file__).resolve().parents[3]
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


# the four public loop edges must keep their identities and use their actual saved axis relations
def AssertSwAxes(SketchValue: Sketch, Resolved: bytes) -> None:
    LoopValue = tuple(f"{SketchValue.id}:profile:0:edge:{Index}" for Index in range(4))
    assert SketchValue.closed_profile_entity_ids == (LoopValue,)
    assert len(SketchValue.parameter_ids) == 2
    Entities = {Entity.id: Entity for Entity in SketchValue.entities}
    AxisRules = [
        RuleValue
        for RuleValue in SketchValue.constraints
        if RuleValue.kind in ("horizontal", "vertical")
    ]
    Targets: set[str] = set()
    for RuleValue in AxisRules:
        (Target,) = RuleValue.references
        Targets.add(Target.entity_id)
        EdgeValue = Entities[Target.entity_id]
        assert Target.point == "" and isinstance(EdgeValue.geometry, LineGeometry)
        assert EdgeValue.provenance is not None and RuleValue.provenance is not None
        (EdgeSpan,) = EdgeValue.provenance.spans
        (RuleSpan,) = RuleValue.provenance.spans
        assert EdgeSpan.record_kind == "sketch-profile-line"
        assert RuleSpan.record_kind == "sketch-axis-relation"
        assert (
            EdgeSpan.stream == RuleSpan.stream == "Contents/Config-0-ResolvedFeatures"
        )
        NativeEdge = int.from_bytes(
            Resolved[EdgeSpan.offset + 6 : EdgeSpan.offset + 10], "little", signed=True
        )
        NativeCode = int.from_bytes(
            Resolved[RuleSpan.offset + 29 : RuleSpan.offset + 33], "little", signed=True
        )
        assert (
            NativeEdge
            == EdgeValue.attributes["native_segment_id"]
            == RuleValue.attributes["native_segment_id"]
        )
        assert (
            NativeCode
            == RuleValue.attributes["native_code"]
            == (4 if RuleValue.kind == "horizontal" else 5)
        )
    assert len(AxisRules) == 4 and Targets == set(LoopValue)


# the archived coincidence must connect the original proxy identity to an endpoint of the preserved loop
def AssertSwOrigin(SketchValue: Sketch, Resolved: bytes) -> None:
    (Saved,) = [
        RuleValue
        for RuleValue in SketchValue.constraints
        if RuleValue.attributes.get("native_code") == 9
    ]
    assert Saved.kind == "coincident" and Saved.provenance is not None
    (RuleSpan,) = Saved.provenance.spans
    assert RuleSpan.stream == "Contents/Config-0-ResolvedFeatures"
    assert RuleSpan.record_kind == "sketch-origin-coincidence"
    assert (
        int.from_bytes(
            Resolved[RuleSpan.offset + 31 : RuleSpan.offset + 35], "little", signed=True
        )
        == 9
    )
    ProxyRef, CornerRef = Saved.references
    assert ProxyRef.point == "" and CornerRef.point == "start"
    Entities = {Entity.id: Entity for Entity in SketchValue.entities}
    Proxy, Corner = Entities[ProxyRef.entity_id], Entities[CornerRef.entity_id]
    assert (
        Proxy.fixed and Proxy.construction and isinstance(Proxy.geometry, PointGeometry)
    )
    assert (
        isinstance(Corner.geometry, LineGeometry)
        and Corner.geometry.start == Proxy.geometry.point
    )
    assert (
        Proxy.attributes["native_origin_feature_id"]
        == Saved.attributes["native_origin_feature_id"]
    )
    assert Proxy.provenance is not None
    (ProxySpan,) = Proxy.provenance.spans
    assert (
        ProxySpan.record_kind == "sketch-point" and ProxySpan.stream == RuleSpan.stream
    )
    assert (
        ProxySpan.offset
        <= int(Proxy.id.rsplit(":", 1)[-1])
        < ProxySpan.offset + ProxySpan.length
    )


# the saved operands must refer to the exact authored edge and preserve the sign of their ordering
def AssertSwDist(
    RuleValue: SketchRelation,
    SketchValue: Sketch,
    ParamValue: Parameter,
    Resolved: bytes,
    Variant: str,
) -> None:
    assert (
        RuleValue.kind == "distance" and RuleValue.driving and not RuleValue.suppressed
    )
    assert RuleValue.attributes["native_code"] == 1 and RuleValue.provenance is not None
    BodySpan, Scalar = RuleValue.provenance.spans
    assert (
        BodySpan.record_kind == "sketch-distance"
        and Scalar.record_kind == "dimension-scalar"
    )
    assert BodySpan.stream == Scalar.stream == "Contents/Config-0-ResolvedFeatures"
    assert Scalar.length == 8 and ParamValue.provenance is not None
    assert ParamValue.provenance.spans == (Scalar,)
    (Metres,) = UnpackFrom("<d", Resolved, Scalar.offset)
    assert ParamValue.value.unit == "mm" and ParamValue.value.value == Metres * 1000
    First, Second = RuleValue.references
    assert First.entity_id == Second.entity_id and {First.point, Second.point} == {
        "start",
        "end",
    }
    assert First.entity_id in SketchValue.closed_profile_entity_ids[0]
    (EdgeValue,) = [
        Value for Value in SketchValue.entities if Value.id == First.entity_id
    ]
    Geometry = EdgeValue.geometry
    assert isinstance(Geometry, LineGeometry)
    Start, Finish = (
        (Geometry.end, Geometry.start)
        if First.point == "end"
        else (Geometry.start, Geometry.end)
    )
    DeltaX, DeltaY = Finish.x - Start.x, Finish.y - Start.y
    assert Hypot(DeltaX, DeltaY) == Metres * 1000
    if Variant == "plane-yz":
        assert (DeltaX, DeltaY) == (
            (0.0, 40.0) if ParamValue.name == "width_mm" else (-20.0, 0.0)
        )
    if Variant == "units-inch":
        assert ParamValue.attributes["source_text"] == (
            "1.57" if ParamValue.name == "width_mm" else "0.79"
        )


# both public driving parameters must own one exact distance in the selected sketch
def AssertSwDists(
    SketchValue: Sketch,
    Parameters: tuple[Parameter, ...],
    Resolved: bytes,
    Variant: str,
) -> None:
    Owned = {
        ItemValue.id: ItemValue
        for ItemValue in Parameters
        if ItemValue.id in SketchValue.parameter_ids
    }
    assert {ItemValue.name for ItemValue in Owned.values()} == {"width_mm", "height_mm"}
    Count = 0
    for RuleValue in SketchValue.constraints:
        if RuleValue.parameter_id is not None:
            AssertSwDist(
                RuleValue,
                SketchValue,
                Owned.pop(RuleValue.parameter_id),
                Resolved,
                Variant,
            )
            Count += 1
    assert not Owned and Count == 2


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
    RootDir = FilePath(__file__).resolve().parents[3]
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
    Resolved = Archive.require(SupportSpan.stream)
    Stored = Resolved[SupportSpan.offset : SupportSpan.offset + SupportSpan.length]
    assert int.from_bytes(Stored, "little", signed=True) == DatumId
    AssertSwAxes(Sketch, Resolved)
    AssertSwOrigin(Sketch, Resolved)
    AssertSwDists(Sketch, Document.parameters, Resolved, Variant)


# a rotated archive uses the reached sketch axis before the saved operation reversal
def AssertSwAxis(Definition: ExtrudeFeature, Variant: str) -> None:
    assert Definition.direction == (
        SpaceVector(1.0, 0.0, 0.0)
        if Variant == "plane-yz"
        else SpaceVector(0.0, 0.0, 1.0)
    )


# native depth and signed direction must survive display unit changes and the public projection
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
        FilePath(__file__).resolve().parents[3]
        / "re/automation/PairedCaptures/P03/solidworks-db1390476325"
        / f"P03-solidworks-{Variant}.SLDPRT"
    )
    Document = OpenDocument(NativePath)
    (BossStep,) = tuple(
        ItemValue
        for ItemValue in Document.feature_timeline
        if ItemValue.name == "BlindBoss"
    )
    Definition = BossStep.definition
    assert isinstance(Definition, ExtrudeFeature)
    Depth = 12 if Variant == "edit-depth_mm-12" else 10
    assert Definition.length is not None
    assert (Definition.length.value, Definition.length.unit) == (Depth, "mm")
    assert Definition.end_condition == ExtrudeEnd.BLIND
    assert Definition.reversed == (Variant == "direction-negative")
    AssertSwAxis(Definition, Variant)
    (SketchValue,) = tuple(
        ItemValue
        for ItemValue in Document.sketches
        if ItemValue.id == BossStep.sketch_id
    )
    assert SketchValue.name == "RectangleSketch"
    assert BossStep.provenance is not None
    Spans = {
        SpanValue.record_kind: SpanValue for SpanValue in BossStep.provenance.spans
    }
    assert Spans["operation-profile-reference"].length == 2
    assert Spans["extrusion-end-spec"].length > 20
    Scalar = Spans["extrusion-depth-scalar"]
    assert Scalar.stream == "Contents/Config-0-ResolvedFeatures" and Scalar.length == 8
    Archive = SldprtArchive.from_bytes(NativePath.read_bytes())
    assert UnpackFrom("<d", Archive.require(Scalar.stream), Scalar.offset) == (
        Depth / 1000,
    )
    (Parameter,) = tuple(
        ItemValue
        for ItemValue in Document.parameters
        if ItemValue.id in BossStep.parameter_ids
    )
    assert (Parameter.name, Parameter.value.value, Parameter.value.unit) == (
        "depth_mm",
        Depth,
        "mm",
    )
    assert Parameter.provenance is not None
    assert [
        (SpanValue.offset, SpanValue.length) for SpanValue in Parameter.provenance.spans
    ] == [(Scalar.offset, 8)]
    AssertBossBody(
        Document, BossStep, Variant, -Depth if Definition.reversed else Depth
    )


# saved boss volume and centroid follow the independent edits and signed extent
def AssertBossBody(
    Document: CadDocument, BossStep: FeatureStep, Variant: str, EndDepth: int
) -> None:
    (BodyValue,) = Document.bodies
    assert BodyValue.final_feature_id == BossStep.id
    assert Document.brep is not None
    assert not Document.brep.validate(frozenset((BodyValue.id,)))
    assert Document.brep.bodies[0].design_body_id == BodyValue.id
    WidthValue = 41 if Variant == "edit-width_mm-41" else 40
    HeightValue = 23 if Variant == "edit-height_mm-23" else 20
    Centre = (WidthValue / 2, HeightValue / 2, EndDepth / 2)
    if Variant == "plane-yz":
        Centre = Centre[2], Centre[0], Centre[1]
    Summary = BodyValue.topology
    assert Summary.solid_count == 1
    assert Summary.volume == Pytest.approx(WidthValue * HeightValue * abs(EndDepth))
    assert BodyValue.attributes["solidworks.body_centroid_mm"] == Pytest.approx(Centre)


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
    RootDir = FilePath(__file__).resolve().parents[3]
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
    RootDir = FilePath(__file__).resolve().parents[3]
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


# sketch only and boss archives use different native addresses for the same witnessed size roles
@Pytest.mark.parametrize(
    ("Family", "Capture", "Variant"),
    (
        ("P01", "5dc3245eb59c", "baseline-a"),
        ("P01", "5dc3245eb59c", "baseline-b"),
        ("P01", "5dc3245eb59c", "edit-width_mm-41"),
        ("P01", "5dc3245eb59c", "edit-height_mm-23"),
        ("P01", "5dc3245eb59c", "plane-yz"),
        ("P01", "5dc3245eb59c", "units-inch"),
        ("P03", "8d53584027ff", "baseline-a"),
        ("P03", "8d53584027ff", "baseline-b"),
        ("P03", "8d53584027ff", "edit-width_mm-41"),
        ("P03", "8d53584027ff", "edit-height_mm-23"),
        ("P03", "8d53584027ff", "edit-depth_mm-12"),
        ("P03", "8d53584027ff", "plane-yz"),
        ("P03", "8d53584027ff", "direction-negative"),
        ("P03", "8d53584027ff", "units-inch"),
    ),
)
def CheckPartRect(Family: str, Capture: str, Variant: str) -> None:
    RootDir = FilePath(__file__).resolve().parents[3]
    Archive = (
        RootDir
        / f"re/automation/PairedCaptures/{Family}/fusion-{Capture}"
        / f"{Family}-fusion-{Variant}.f3d"
    )
    Document = OpenDocument(Archive, StrictMode=False)
    (SketchValue,) = Document.sketches
    Selected = Family == "P03"
    Prefix = "fusion.selected_profile" if Selected else "fusion.authored_contour"
    assert (
        SketchValue.attributes.get(f"{Prefix}_size_corner_object_id") == 228
    ), Document.diagnostics
    Entities = {f"fusion-sketch-entity-{Identity}" for Identity in (232, 238, 244, 248)}
    if Selected:
        AssertBossOrder(Document, Variant)
        (LoopValue,) = SketchValue.closed_profile_entity_ids
        assert set(LoopValue) == Entities
    else:
        assert SketchValue.closed_profile_entity_ids == ()
        assert SketchValue.attributes["fusion.authored_contour_entity_ids"] == tuple(
            f"fusion-sketch-entity-{Identity}" for Identity in (232, 238, 244, 248)
        )
        assert not any(
            KeyValue.startswith("fusion.selected_profile")
            for Relation in SketchValue.constraints
            for KeyValue in Relation.attributes
        )
    AssertPartDims(Document, SketchValue, Prefix, Selected, Variant)


# signed extrude direction and rotated sketch frames retain distinct saved membership orders
def AssertBossOrder(Document: CadDocument, Variant: str) -> None:
    Feature = Document.feature_timeline[-1]
    assert Feature.attributes["fusion.profile_selection_proxy_id"] == 278
    assert Feature.attributes["fusion.profile_descriptor_id"] == 281
    Order = {
        "plane-yz": (248, 232, 238, 244),
        "direction-negative": (232, 248, 238, 244),
    }.get(Variant, (248, 238, 244, 232))
    assert Feature.attributes["fusion.profile_native_members"] == tuple(
        f"fusion-sketch-entity-{Identity}" for Identity in Order
    )


# saved width and height point order identifies the real axis rule and graph row
def AssertPartDims(
    Document: CadDocument,
    SketchValue: Sketch,
    Prefix: str,
    Selected: bool,
    Variant: str,
) -> None:
    Names = {Value.id: Value.name for Value in Document.parameters}
    Dimensions = {
        Names[Value.parameter_id]: Value
        for Value in SketchValue.constraints
        if Value.parameter_id is not None
    }
    AxisRules = {
        Value.id: Value
        for Value in SketchValue.constraints
        if Value.kind in ("horizontal", "vertical")
    }
    assert len(AxisRules) == 4 and set(Dimensions) == {"width_mm", "height_mm"}
    assert {Value.attributes[f"{Prefix}_side_id"] for Value in AxisRules.values()} == {
        f"fusion-sketch-entity-{Identity}" for Identity in (232, 238, 244, 248)
    }
    KindKey = "loop" if Selected else "sketch"
    for NameValue, SideId, BindId, EndIds in (
        ("width_mm", 232, 259, (228, 230)),
        ("height_mm", 248, 269 if Selected else 266, (242, 228)),
    ):
        Relation = Dimensions[NameValue]
        Attributes = Relation.attributes
        assert Attributes[f"{Prefix}_side_id"] == f"fusion-sketch-entity-{SideId}"
        assert Attributes[f"{Prefix}_{KindKey}_object_id"] == (284 if Selected else 202)
        assert Attributes[f"{Prefix}_binding_edge"] == (207, BindId, 1)
        assert tuple(Value.entity_id for Value in Relation.references) == tuple(
            f"fusion-sketch-entity-{Identity}" for Identity in EndIds
        )
        AxisId = Attributes[f"{Prefix}_axis_relation_id"]
        assert isinstance(AxisId, str)
        Horizontal = (NameValue == "width_mm") != (Variant == "plane-yz")
        assert AxisRules[AxisId].kind == ("horizontal" if Horizontal else "vertical")


# the saved boss cap would misleadingly look like an origin plane without its selection records
def CheckFaceDatum() -> None:
    RootDir = FilePath(__file__).resolve().parents[3]
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


# both editable centering values must retain the particular dimension handles stored in config
@Pytest.mark.parametrize("Variant", KCutVariants)
def CheckSwCutEq(Variant: str) -> None:
    NativePath = (
        FilePath(__file__).resolve().parents[3]
        / "re/automation/PairedCaptures/P04/solidworks-c1986308375a"
        / f"P04-solidworks-{Variant}.SLDPRT"
    )
    Document = OpenDocument(NativePath)
    Archive = SldprtArchive.from_bytes(NativePath.read_bytes())
    Stream = Archive.require("Contents/Config-0")
    Params = {Value.id: Value for Value in Document.parameters}
    WidthValue = 44 if Variant == "edit-width_mm-44" else 40
    CutWidth = 12 if Variant == "edit-cut_width_mm-12" else 10
    HeightValue = 24 if Variant == "edit-height_mm-24" else 20
    CutHeight = 10 if Variant == "edit-cut_height_mm-10" else 8
    for Target, OuterName, InnerName, OuterValue, InnerValue, Slots in (
        ("cut_left_mm", "width_mm", "cut_width_mm", WidthValue, CutWidth, (2, 0, 0)),
        (
            "cut_bottom_mm",
            "height_mm",
            "cut_height_mm",
            HeightValue,
            CutHeight,
            (3, 1, 1),
        ),
    ):
        TargetValue = Params[f"sldprt:parameter:35:{Target}"]
        OuterId = f"sldprt:parameter:26:{OuterName}"
        InnerId = f"sldprt:parameter:35:{InnerName}"
        assert Params[OuterId].value.value == Pytest.approx(OuterValue)
        assert Params[InnerId].value.value == Pytest.approx(InnerValue)
        assert TargetValue.value.value == Pytest.approx((OuterValue - InnerValue) / 2)
        assert TargetValue.value.unit == "mm" and TargetValue.expression is not None
        assert TargetValue.expression.parameter_ids == (OuterId, InnerId)
        assert TargetValue.provenance is not None
        Spans = {Value.record_kind: Value for Value in TargetValue.provenance.spans}
        for RecordKind, SlotValue in zip(
            ("equation-target-slot", "equation-outer-slot", "equation-inner-slot"),
            Slots,
            strict=True,
        ):
            SpanValue = Spans[RecordKind]
            assert (SpanValue.stream, SpanValue.length) == ("Contents/Config-0", 4)
            assert UnpackFrom("<i", Stream, SpanValue.offset) == (SlotValue,)


# blind and through all trims must expose their exact target and distinct length framing
@Pytest.mark.parametrize("Variant", KCutVariants)
def CheckSwCutOp(Variant: str) -> None:
    NativePath = (
        FilePath(__file__).resolve().parents[3]
        / "re/automation/PairedCaptures/P04/solidworks-c1986308375a"
        / f"P04-solidworks-{Variant}.SLDPRT"
    )
    Document = OpenDocument(NativePath)
    Through = Variant == "termination-through-all"
    (CutStep,) = tuple(
        Value
        for Value in Document.feature_timeline
        if Value.name == ("ThroughAllCut" if Through else "BlindCut")
    )
    Definition = CutStep.definition
    assert isinstance(Definition, ExtrudeFeature)
    assert Definition.reversed
    AssertSwAxis(Definition, Variant)
    assert Definition.end_condition == (
        ExtrudeEnd.THROUGH_ALL if Through else ExtrudeEnd.BLIND
    )
    assert CutStep.sketch_id == "sldprt:sketch:35"
    assert CutStep.input_feature_ids == ("sldprt:feature:34", "sldprt:feature:35")
    (Target,) = tuple(
        Value for Value in Document.selections if Value.id in CutStep.selection_ids
    )
    (BodyPath,) = Target.path
    assert (BodyPath.entity_id, BodyPath.subelement) == (
        "sldprt:feature:34",
        "body:101",
    )
    assert Target.query["topology_role"] == "historical_cut_target"
    assert Target.provenance is not None and CutStep.provenance is not None
    Spans = {Value.record_kind: Value for Value in CutStep.provenance.spans}
    (BodySpan,) = Target.provenance.spans
    assert BodySpan == Spans["cut-target-body"] and BodySpan.length > 100
    Archive = SldprtArchive.from_bytes(NativePath.read_bytes())
    AssertCutDepth(Archive, Document, CutStep, Definition, Variant)
    AssertSwCutFace(Variant, Document)
    AssertCutRules(Variant, Document, Archive.require("Contents/Config-0"))


# the blind parameter and through all absence must match saved raw bytes
def AssertCutDepth(
    Archive: SldprtArchive,
    Document: CadDocument,
    CutStep: FeatureStep,
    Definition: ExtrudeFeature,
    Variant: str,
) -> None:
    assert CutStep.provenance is not None
    Spans = {Value.record_kind: Value for Value in CutStep.provenance.spans}
    if Variant == "termination-through-all":
        assert Definition.length is None and not CutStep.parameter_ids
        Unset = Spans["extrusion-depth-absent"]
        assert UnpackFrom("<H", Archive.require(Unset.stream), Unset.offset) == (0,)
        return
    DepthValue = 5 if Variant == "edit-cut_depth_mm-5" else 4
    assert Definition.length is not None
    assert (Definition.length.value, Definition.length.unit) == (DepthValue, "mm")
    (ParamValue,) = tuple(
        Value for Value in Document.parameters if Value.id in CutStep.parameter_ids
    )
    assert ParamValue.name == "cut_depth_mm"
    Scalar = Spans["extrusion-depth-scalar"]
    assert UnpackFrom("<d", Archive.require(Scalar.stream), Scalar.offset) == (
        DepthValue / 1000,
    )


# the public cut frame must retain the historical face and rotated archived axes
def AssertSwCutFace(Variant: str, Document: CadDocument) -> None:
    (SketchValue,) = tuple(
        Value for Value in Document.sketches if Value.id == "sldprt:sketch:35"
    )
    assert SketchValue.attributes["support_plane_source"] == "typed-archive-face"
    PlaneId = SketchValue.support_plane_id
    (Frame,) = tuple(Value for Value in Document.support_planes if Value.id == PlaneId)
    DepthValue = 12 if Variant == "edit-depth_mm-12" else 10
    IsRotated = Variant == "plane-yz"
    assert Frame.transform.origin == SpaceVector(
        *((DepthValue, 0, 0) if IsRotated else (0, 0, DepthValue))
    )
    assert Frame.transform.x_axis == SpaceVector(
        *((0, 0, -1) if IsRotated else (1, 0, 0))
    )
    assert Frame.transform.z_axis == SpaceVector(
        *((1, 0, 0) if IsRotated else (0, 0, 1))
    )
    (FacePick,) = tuple(
        Value for Value in Document.selections if Value.id == Frame.support_selection_id
    )
    (FacePath,) = FacePick.path
    assert (FacePath.entity_id, FacePath.subelement) == (
        "sldprt:feature:34",
        "end-face:1",
    )
    assert FacePick.query["native_ordered_edge_occurrences"] == (
        (4, 3, 2, 1) if IsRotated else (4, 1, 2, 3)
    )
    assert FacePick.provenance is not None
    assert all(
        Value.stream == "Contents/Config-0-ResolvedFeatures"
        for Value in FacePick.provenance.spans
    )
    AssertSwCutLoop(SketchValue)


# the typed local perimeter retains native line records in their directed closure
def AssertSwCutLoop(SketchValue: Sketch) -> None:
    Lines = tuple(
        Value
        for Value in SketchValue.entities
        if isinstance(Value.geometry, LineGeometry)
    )
    assert tuple(Value.attributes.get("native_segment_id") for Value in Lines) == (
        1,
        4,
        3,
        2,
    )
    assert SketchValue.closed_profile_entity_ids == (
        tuple(Value.id for Value in Lines),
    )
    Shapes: list[LineGeometry] = []
    for LineValue in Lines:
        assert LineValue.provenance is not None and isinstance(
            LineValue.geometry, LineGeometry
        )
        Shapes.append(LineValue.geometry)
        (SpanValue,) = LineValue.provenance.spans
        assert (SpanValue.stream, SpanValue.record_kind) == (
            "Contents/Config-0",
            "config-sketch-line",
        )
    assert [Value.end for Value in Shapes] == [
        Value.start for Value in Shapes[1:] + Shapes[:1]
    ]


# the earlier rectangle must preserve separate configuration geometry and resolved datum sources
@Pytest.mark.parametrize("Variant", KCutVariants)
def CheckSwOuter(Variant: str) -> None:
    NativePath = (
        FilePath(__file__).resolve().parents[3]
        / "re/automation/PairedCaptures/P04/solidworks-c1986308375a"
        / f"P04-solidworks-{Variant}.SLDPRT"
    )
    Document = OpenDocument(NativePath)
    (SketchValue,) = tuple(
        Value for Value in Document.sketches if Value.id == "sldprt:sketch:26"
    )
    (Frame,) = tuple(
        Value
        for Value in Document.support_planes
        if Value.id == SketchValue.support_plane_id
    )
    DatumId = 4 if Variant == "plane-yz" else 2
    assert Frame.name == ("Right Plane" if DatumId == 4 else "Front Plane")
    assert SketchValue.attributes["support_plane_source"] == "typed-archive-reference"
    assert Frame.transform.z_axis == SpaceVector(
        *((1, 0, 0) if DatumId == 4 else (0, 0, 1))
    )
    assert SketchValue.provenance is not None
    Support = next(
        Value
        for Value in SketchValue.provenance.spans
        if Value.record_kind == "sketch-support-reference"
    )
    Archive = SldprtArchive.from_bytes(NativePath.read_bytes())
    assert (
        Support.stream == "Contents/Config-0-ResolvedFeatures" and Support.length == 4
    )
    assert UnpackFrom("<i", Archive.require(Support.stream), Support.offset) == (
        DatumId,
    )
    AssertOuterLoop(SketchValue)
    AssertOuterDims(Document, SketchValue, Archive, Variant)
    AssertOuterBoss(Document, Variant)


# the configured loop must expose the authored axes and projected origin binding
def AssertOuterLoop(SketchValue: Sketch) -> None:
    (LoopValue,) = SketchValue.closed_profile_entity_ids
    Lines = [Value for Value in SketchValue.entities if Value.id in LoopValue]
    assert len(Lines) == 4
    assert tuple(Value.attributes["native_segment_id"] for Value in Lines) == (
        1,
        4,
        3,
        2,
    )
    for LineValue in Lines:
        assert LineValue.provenance is not None and isinstance(
            LineValue.geometry, LineGeometry
        )
        (Source,) = LineValue.provenance.spans
        assert (Source.stream, Source.record_kind) == (
            "Contents/Config-0",
            "sketch-profile-line",
        )
    AxisRules = [
        Value
        for Value in SketchValue.constraints
        if Value.kind in ("horizontal", "vertical")
    ]
    assert len(AxisRules) == 4 and {
        Value.references[0].entity_id for Value in AxisRules
    } == set(LoopValue)
    (Origin,) = tuple(
        Value for Value in SketchValue.constraints if Value.kind == "coincident"
    )
    assert Origin.provenance is not None
    assert Origin.references[1].entity_id in LoopValue
    (Proxy,) = tuple(
        Value
        for Value in SketchValue.entities
        if Value.id == Origin.references[0].entity_id
    )
    assert (
        Proxy.construction and Proxy.fixed and isinstance(Proxy.geometry, PointGeometry)
    )


# the two width and height values must read the exact configured scalars and endpoint operands
def AssertOuterDims(
    Document: CadDocument, SketchValue: Sketch, Archive: SldprtArchive, Variant: str
) -> None:
    Parameters = {
        Value.name: Value
        for Value in Document.parameters
        if Value.id in SketchValue.parameter_ids
    }
    assert set(Parameters) == {"width_mm", "height_mm"}
    for NameValue, Millimetres in (
        ("width_mm", 44 if Variant == "edit-width_mm-44" else 40),
        ("height_mm", 24 if Variant == "edit-height_mm-24" else 20),
    ):
        Parameter = Parameters[NameValue]
        assert Parameter.value.unit == "mm" and Parameter.value.value == Pytest.approx(
            Millimetres
        )
        (RuleValue,) = tuple(
            Value
            for Value in SketchValue.constraints
            if Value.parameter_id == Parameter.id
        )
        assert RuleValue.driving and len(RuleValue.references) == 2
        assert Parameter.provenance is not None and RuleValue.provenance is not None
        (Scalar,) = Parameter.provenance.spans
        assert Scalar.stream == "Contents/Config-0" and Scalar.length == 8
        assert Scalar in RuleValue.provenance.spans
        assert UnpackFrom("<d", Archive.require(Scalar.stream), Scalar.offset) == (
            Millimetres / 1000,
        )


# the earlier body must keep the saved rectangle owner and its authored length
def AssertOuterBoss(Document: CadDocument, Variant: str) -> None:
    (BossStep,) = tuple(
        Value for Value in Document.feature_timeline if Value.name == "BlindBoss"
    )
    assert BossStep.sketch_id == "sldprt:sketch:26"
    Definition = BossStep.definition
    assert isinstance(Definition, ExtrudeFeature) and not Definition.reversed
    AssertSwAxis(Definition, Variant)
    assert Definition.length is not None
    assert (Definition.length.value, Definition.length.unit) == (
        12 if Variant == "edit-depth_mm-12" else 10,
        "mm",
    )
    assert BossStep.provenance is not None
    assert {Value.record_kind for Value in BossStep.provenance.spans} >= {
        "operation-profile-reference",
        "extrusion-end-spec",
        "extrusion-depth-scalar",
    }


# the active partition owns the saved body even when a profile packet also decodes
@Pytest.mark.parametrize("Variant", KCutVariants)
def CheckSwPart(Variant: str) -> None:
    NativePath = (
        FilePath(__file__).resolve().parents[3]
        / "re/automation/PairedCaptures/P04/solidworks-c1986308375a"
        / f"P04-solidworks-{Variant}.SLDPRT"
    )
    Document = OpenDocument(NativePath)
    (BodyValue,) = Document.bodies
    assert Document.brep is not None and not Document.brep.validate(
        frozenset((BodyValue.id,))
    )
    (Stored,) = Document.brep.bodies
    assert Stored.design_body_id == BodyValue.id
    Summary = BodyValue.topology
    assert Summary.bounding_box is not None
    Count = 10 if Variant == "termination-through-all" else 11
    assert (Summary.solid_count, Summary.shell_count, Summary.face_count) == (
        1,
        1,
        Count,
    )
    assert (Summary.edge_count, Summary.vertex_count) == (24, 16)
    PayloadId = BodyValue.attributes["parasolid_active_payload_id"]
    (Payload,) = tuple(
        Value for Value in Document.brep_payloads if Value.id == PayloadId
    )
    assert (Payload.source_stream, Payload.kind) == (
        "Contents/Config-0-Partition",
        "partition",
    )
    assert any(
        Value.source_stream == "Contents/Config-0-ResolvedFeatures"
        for Value in Document.brep_payloads
    )
    WidthValue = 44 if Variant == "edit-width_mm-44" else 40
    HeightValue = 24 if Variant == "edit-height_mm-24" else 20
    DepthValue = 12 if Variant == "edit-depth_mm-12" else 10
    Maximum = (
        (DepthValue, WidthValue, HeightValue)
        if Variant == "plane-yz"
        else (WidthValue, HeightValue, DepthValue)
    )
    assert Summary.bounding_box.minimum == SpaceVector(0, 0, 0)
    assert Summary.bounding_box.maximum == SpaceVector(*Maximum)
    AssertSwMass(Document, Variant, (WidthValue, HeightValue, DepthValue))


# the saved solid measures must agree with the independently specified rectangle and cut sizes
def AssertSwMass(
    Document: CadDocument, Variant: str, OuterSize: tuple[int, int, int]
) -> None:
    WidthValue, HeightValue, DepthValue = OuterSize
    CutWidth = 12 if Variant == "edit-cut_width_mm-12" else 10
    CutHeight = 10 if Variant == "edit-cut_height_mm-10" else 8
    CutDepth = {
        "edit-cut_depth_mm-5": 5,
        "termination-through-all": DepthValue,
    }.get(Variant, 4)
    assert Document.brep is not None
    ThroughAll = Variant == "termination-through-all"
    GrossArea = WidthValue * HeightValue
    HoleArea = CutWidth * CutHeight
    VerifySwLoops(Document.brep, GrossArea, HoleArea, 2 if ThroughAll else 1)
    if ThroughAll:
        VerifySwExport(Document.brep, GrossArea, HoleArea)
    Gross = WidthValue * HeightValue * DepthValue
    Removed = CutWidth * CutHeight * CutDepth
    Volume = Gross - Removed
    Centre = (
        WidthValue / 2,
        HeightValue / 2,
        (Gross * DepthValue / 2 - Removed * (DepthValue - CutDepth / 2)) / Volume,
    )
    if Variant == "plane-yz":
        Centre = Centre[2], Centre[0], Centre[1]
    (BodyValue,) = Document.bodies
    assert BodyValue.topology.volume == Pytest.approx(Volume)
    assert BodyValue.attributes["solidworks.body_centroid_mm"] == Pytest.approx(Centre)


# the archived origin proxy must keep both its local point and earlier feature ownership
def AssertCutOrigin(Document: CadDocument, SketchValue: Sketch) -> None:
    (Proxy,) = tuple(
        Value
        for Value in SketchValue.entities
        if isinstance(Value.geometry, PointGeometry)
    )
    assert (
        Proxy.fixed and Proxy.construction and isinstance(Proxy.geometry, PointGeometry)
    )
    assert (Proxy.geometry.point.x, Proxy.geometry.point.y) == (0.0, 0.0)
    assert Proxy.attributes["native_point_id"] == (4, 5)
    assert Proxy.attributes["native_origin_point_handle"] == (0, -1, 0)
    assert Proxy.provenance is not None
    assert tuple(SpanValue.record_kind for SpanValue in Proxy.provenance.spans) == (
        "cut-origin-proxy-point",
        "origin-source-point",
    )
    PickId = Proxy.attributes["solidworks.projection_source_selection_id"]
    (OriginPick,) = tuple(Value for Value in Document.selections if Value.id == PickId)
    (OriginPath,) = OriginPick.path
    assert (OriginPath.entity_id, OriginPath.subelement) == (
        "sldprt:feature:5",
        "point:0",
    )
    (Owner,) = tuple(
        Value for Value in Document.feature_timeline if Value.id == "sldprt:feature:35"
    )
    assert (
        OriginPick.id in Owner.selection_ids
        and OriginPath.entity_id in Owner.input_feature_ids
    )


# an axis record must bind a typed line rather than an equivalently numbered trim edge
def AssertCutAxis(RuleValue: SketchRelation, SketchValue: Sketch, Config: bytes) -> int:
    (Reference,) = RuleValue.references
    assert Reference.point == ""
    (LineValue,) = tuple(
        Value for Value in SketchValue.entities if Value.id == Reference.entity_id
    )
    assert isinstance(LineValue.geometry, LineGeometry)
    assert LineValue.provenance is not None and RuleValue.provenance is not None
    (LineSpan,) = LineValue.provenance.spans
    (RuleSpan,) = RuleValue.provenance.spans
    assert RuleSpan.stream == LineSpan.stream == "Contents/Config-0"
    assert RuleSpan.record_kind == "sketch-axis-relation"
    (NativeId,) = UnpackFrom("<i", Config, LineSpan.offset + 6)
    (TypeCode,) = UnpackFrom("<i", Config, RuleSpan.offset + 29)
    assert isinstance(NativeId, int)
    assert NativeId == RuleValue.attributes["native_segment_id"]
    assert (
        TypeCode
        == RuleValue.attributes["native_code"]
        == (4 if RuleValue.kind == "horizontal" else 5)
    )
    return NativeId


# each saved value and role must bind to the ordered configuration point operands
def AssertCutDist(
    Variant: str, RuleValue: SketchRelation, ParamValue: Parameter, Config: bytes
) -> None:
    assert RuleValue.provenance is not None and ParamValue.provenance is not None
    BodySpan, Scalar = RuleValue.provenance.spans
    assert BodySpan.record_kind == "sketch-distance"
    assert BodySpan.stream == Scalar.stream == "Contents/Config-0"
    assert Scalar in ParamValue.provenance.spans and Scalar.length == 8
    assert ParamValue.value.value == UnpackFrom("<d", Config, Scalar.offset)[0] * 1000
    assert ParamValue.value.unit == "mm"
    First, Second = RuleValue.references
    Named = ParamValue.name
    if Named in ("cut_width_mm", "cut_height_mm"):
        assert (
            RuleValue.kind == "distance"
            and RuleValue.driving
            and ParamValue.role == "driving"
        )
        assert First.entity_id == Second.entity_id and {First.point, Second.point} == {
            "start",
            "end",
        }
        return
    assert Named in ("cut_left_mm", "cut_bottom_mm") and ParamValue.role == "derived"
    assert not RuleValue.driving and ParamValue.expression is not None
    assert RuleValue.attributes["native_point_ids"] == ((4, 5), (0, 1))
    assert (
        First.entity_id.endswith(":native-point:5")
        and First.point == ""
        and Second.point == "start"
    )
    IsRotated = Variant == "plane-yz"
    assert RuleValue.kind == (
        "distance_x" if (Named == "cut_left_mm") != IsRotated else "distance_y"
    )
    assert RuleValue.attributes["solidworks.signed_distance_multiplier"] == (
        -1 if IsRotated and Named == "cut_bottom_mm" else 1
    )


# every cut capture must retain its four measured line targets and four typed value bindings
def AssertCutRules(Variant: str, Document: CadDocument, Config: bytes) -> None:
    (SketchValue,) = tuple(
        Value for Value in Document.sketches if Value.id == "sldprt:sketch:35"
    )
    assert len(SketchValue.constraints) == 8
    AssertCutOrigin(Document, SketchValue)
    Parameters = {
        Value.id: Value
        for Value in Document.parameters
        if Value.id in SketchValue.parameter_ids
    }
    AxisIds: set[int] = set()
    for RuleValue in SketchValue.constraints:
        if RuleValue.parameter_id is None:
            AxisIds.add(AssertCutAxis(RuleValue, SketchValue, Config))
        else:
            AssertCutDist(
                Variant, RuleValue, Parameters.pop(RuleValue.parameter_id), Config
            )
    assert not Parameters and AxisIds == {1, 2, 3, 4}


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
    RootDir = FilePath(__file__).resolve().parents[3]
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
        assert LineValue.attributes["fusion.cap_curve_state"] == (0x10000, 0)
        assert not LineValue.fixed and not LineValue.construction
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
    AssertCutBody(Variant, Cutter, Document)


# final saved topology must follow the cut actor and the visible native body rather than its prior boss chart
def AssertCutBody(Variant: str, Cutter: FeatureStep, Document: CadDocument) -> None:
    assert len(Document.bodies) == 1, Document.diagnostics
    (BodyValue,) = Document.bodies
    assert BodyValue.final_feature_id == Cutter.id
    assert BodyValue.provenance is not None and BodyValue.provenance.native_id == "309"
    assert BodyValue.attributes["fusion.geometry_source"] == "saved_cut_result_topology"
    assert BodyValue.attributes["fusion.history_body_result_ordinal"] == 1
    assert BodyValue.attributes["fusion.native_body_collection_id"] == 7
    assert BodyValue.topology.solid_count == BodyValue.topology.shell_count == 1
    assert BodyValue.topology.face_count == (
        10 if Variant == "termination-through-all" else 11
    )
    assert BodyValue.topology.edge_count == 24 and BodyValue.topology.vertex_count == 16
    Bounds = BodyValue.topology.bounding_box
    assert Bounds is not None and Bounds.minimum == SpaceVector(0.0, 0.0, 0.0)
    Expected = {
        "edit-width_mm-44": (44.0, 20.0, 10.0),
        "edit-height_mm-24": (40.0, 24.0, 10.0),
        "edit-depth_mm-12": (40.0, 20.0, 12.0),
        "plane-yz": (10.0, 40.0, 20.0),
    }.get(Variant, (40.0, 20.0, 10.0))
    assert (Bounds.maximum.x, Bounds.maximum.y, Bounds.maximum.z) == Pytest.approx(
        Expected
    )
    assert Capability.KBodyStructure in Document.capabilities
    assert Document.brep is None and Capability.KBrep not in Document.capabilities


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
    AssertRectCtrl(Variant, Document)


# saved member order and native bound side identity are independent controls
def AssertRectCtrl(Variant: str, Document: CadDocument) -> None:
    Params = {Value.id: Value.name for Value in Document.parameters}
    Features = {
        Value.provenance.native_id: Value
        for Value in Document.feature_timeline
        if Value.provenance is not None
    }
    Orders = {
        "plane-yz": ((248, 232, 238, 244), (400, 399, 393, 396)),
        "termination-through-all": ((248, 244, 238, 232), (400, 399, 396, 393)),
    }
    BossOrder, CutOrder = Orders.get(
        Variant, ((232, 248, 238, 244), (400, 396, 393, 399))
    )
    Sketches = {Value.id: Value for Value in Document.sketches}
    for FeatureId, MemberOrder, LoopId, CornerId in (
        ("277", BossOrder, 284, 228),
        ("446", CutOrder, 460, 389),
    ):
        StepValue = Features[FeatureId]
        assert StepValue.attributes["fusion.profile_native_members"] == tuple(
            f"fusion-sketch-entity-{Identity}" for Identity in MemberOrder
        )
        SketchValue = Sketches[StepValue.sketch_id or ""]
        assert (
            SketchValue.attributes.get("fusion.selected_profile_size_corner_object_id")
            == CornerId
        ), Document.diagnostics
        AssertRectAxes(SketchValue, LoopId, MemberOrder)
        AssertRectDims(SketchValue, Params, LoopId)


# each axis relation retains the exact selected side from its original operand
def AssertRectAxes(
    SketchValue: Sketch, LoopId: int, MemberOrder: tuple[int, ...]
) -> None:
    AxisSides = {
        Value.references[0].entity_id
        for Value in SketchValue.constraints
        if Value.kind in ("horizontal", "vertical")
        and Value.attributes.get("fusion.selected_profile_side_id")
        == Value.references[0].entity_id
        and Value.attributes.get("fusion.selected_profile_loop_object_id") == LoopId
    }
    assert AxisSides == {f"fusion-sketch-entity-{Identity}" for Identity in MemberOrder}


# size dimensions preserve their literal graph links and center dimensions retain independent operands
def AssertRectDims(SketchValue: Sketch, Params: dict[str, str], LoopId: int) -> None:
    Expected = {
        "width_mm": (232, 252, (207, 259, 1)),
        "height_mm": (248, 255, (207, 269, 1)),
        "cut_width_mm": (393, 401, (334, 432, 1)),
        "cut_height_mm": (400, 404, (334, 436, 1)),
    }
    for Relation in SketchValue.constraints:
        if Relation.parameter_id is None:
            continue
        Control = Expected.get(Params[Relation.parameter_id])
        Attributes = Relation.attributes
        if Control is None:
            assert "fusion.selected_profile_side_id" not in Attributes
            continue
        SideId, RuleId, Binding = Control
        assert (
            Attributes["fusion.selected_profile_side_id"]
            == f"fusion-sketch-entity-{SideId}"
        )
        assert (
            Attributes["fusion.selected_profile_axis_relation_id"]
            == f"fusion-sketch-relation-{RuleId}"
        )
        assert Attributes["fusion.selected_profile_loop_object_id"] == LoopId
        assert Attributes["fusion.selected_profile_binding_edge"] == Binding


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
    RootDir = FilePath(__file__).resolve().parents[3]
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
