from struct import pack as PackData

from pytest import raises as Raises

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.RevolveAxis import ResolveRevAxis
from convert.formats.Fusion.Revolves.RevolveRead import ReadRevInputs
from convert.formats.Fusion.SelectionProxy import KSelectProxy
from convert.formats.Fusion.SelectionRef import KSelectDesc, KSelectLeaf, ReadEntityRef
from convert.formats.Fusion.Sketches.SketchPick import KSketchLeaf
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumGeometry import GeometryKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.records.RecordProvenance import Provenance
from tests.convert.formats.FusionHistoryTests import NativeRef
from tests.convert.formats.FusionParamTests import NativeText


# the wire puts target two ahead of target one regardless of the selection order
def TestTargetOrder() -> None:
    Header = PackData("<IIBBBBB", 4, 1, 0, 0, 1, 0, 0)
    BodyValue = (
        bytes(2)
        + Header
        + b"\0"
        + NativeRef(10)
        + NativeRef(20)
        + NativeRef(30)
        + NativeRef(40)
        + NativeRef(50)
    )
    Controls = ReadRevInputs(BodyValue)
    assert Controls.ExtentKind == "to_entity"
    assert Controls.SideMode == "two_sided"
    assert Controls.AlongId == 10
    assert Controls.AgainstId is None
    assert Controls.AxisId == 20
    assert Controls.TargetIds == (50, 30)
    with Raises(ValueError, match="Truncated"):
        _ = ReadRevInputs(BodyValue[:-1])


# a common descriptor can select either a construction object or a sketch tag
def SelectFixture(
    LeafGuid: str, LeafBody: bytes
) -> tuple[bytearray, dict[int, RecordSpan]]:
    GuidBytes = NativeText("12345678-1234-1234-1234-123456789abc")
    BulkData = bytearray()
    Owners: dict[int, RecordSpan] = {}
    for Identity, ClassGuid, BodyValue in (
        (
            20,
            KSelectProxy,
            bytes(2) + PackData("<I", 1) + NativeRef(21) + bytes(66) + NativeRef(10),
        ),
        (
            21,
            KSelectDesc,
            bytes(2)
            + NativeRef(22)
            + PackData("<I", 1)
            + GuidBytes * 2
            + bytes(83)
            + NativeRef(10),
        ),
        (22, LeafGuid, LeafBody),
    ):
        Offset = len(BulkData)
        BulkData.extend(bytes(4) + BodyValue)
        Owners[Identity] = RecordSpan(
            Offset, Offset, len(BulkData), Identity, 256, ClassGuid, "", True
        )
    return BulkData, Owners


# both reciprocal owner references must identify the same feature
def TestOwnedSelect() -> None:
    BulkData, Owners = SelectFixture(KSelectLeaf, bytes(2) + PackData("<Q", 30))
    assert ReadEntityRef(bytes(BulkData), Owners, 20, 10) == (21, 22, 30)
    OwnerOffset = Owners[21].EndOffset - 11
    BulkData[OwnerOffset : OwnerOffset + 11] = NativeRef(99)
    with Raises(ValueError, match="descriptor owner"):
        _ = ReadEntityRef(bytes(BulkData), Owners, 20, 10)


# a sketch pick keeps its directed entity and depends only on a preceding sketch
def TestSketchAxis() -> None:
    BulkData, Owners = SelectFixture(KSketchLeaf, bytes(10) + PackData("<QQ", 40, 50))
    Entity = SketchEntity(
        id="line",
        kind=GeometryKind.KLine,
        geometry=LineGeometry(PlaneVector(1.0, 2.0), PlaneVector(-2.0, 1.0)),
        provenance=Provenance(adapter="fusion.f3d", native_id="30"),
        attributes=FreezeMapping({"fusion.entity_tag": 50}),
    )
    Source = Sketch(
        id="axis-sketch",
        name="Axis sketch",
        support_plane_id="plane",
        entities=(Entity,),
    )
    SourceStep = FeatureStep("source", "Axis sketch", FeatureKind.KNative, 2)
    Links = {40: (Source, SourceStep)}
    Result = ResolveRevAxis(bytes(BulkData), Owners, 20, 10, 3, Links, {})
    assert Result.ObjectId == 30
    assert Result.DependencyId == SourceStep.id
    assert tuple(
        (ElementValue.entity_kind, ElementValue.entity_id)
        for ElementValue in Result.PathElems
    ) == (
        ("sketch", Source.id),
        ("sketch_entity", Entity.id),
    )
    with Raises(ValueError, match="outside prior history"):
        _ = ResolveRevAxis(bytes(BulkData), Owners, 20, 10, 1, Links, {})
