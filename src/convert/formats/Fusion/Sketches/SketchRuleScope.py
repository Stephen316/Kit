from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.SketchPrimitive import KSketchKinds
from convert.formats.Fusion.Sketches.SketchRuleIds import KSketchRoot
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.Sketch import Sketch, SketchEntity


# neutral sketches must preserve the exact typed root identity from source projection
def ReadSketchRoot(SketchValue: Sketch, Owners: dict[int, RecordSpan]) -> RecordSpan:
    Origin = SketchValue.provenance
    if Origin is None or Origin.adapter != "fusion.f3d":
        raise ValueError("Missing native Fusion sketch provenance")
    OwnerId = int(Origin.native_id)
    RootSpan = Owners.get(OwnerId)
    if (
        Origin.native_id != str(OwnerId)
        or SketchValue.id != f"fusion-sketch-{OwnerId}"
        or RootSpan is None
        or RootSpan.ClassGuid != KSketchRoot
        or not RootSpan.IsPrimary
    ):
        raise ValueError("Fusion sketch relation owner is unresolved")
    return RootSpan


# endpoint and curve targets must resolve by native identity in the same sketch
def IndexRuleEnts(
    BulkData: bytes, Owners: dict[int, RecordSpan], SketchValue: Sketch, OwnerId: int
) -> dict[int, SketchEntity]:
    Entities: dict[int, SketchEntity] = {}
    for Entity in SketchValue.entities:
        Origin = Entity.provenance
        if (
            Origin is None
            or Origin.adapter != "fusion.f3d"
            or not Origin.native_id.isascii()
            or not Origin.native_id.isdigit()
            or len(Origin.native_id) > 20
        ):
            continue
        EntityId = int(Origin.native_id)
        SpanValue = Owners.get(EntityId)
        KindValue = (
            GeometryKind.KCircle
            if Entity.kind == GeometryKind.KArcGeometry
            else Entity.kind
        )
        if (
            Origin.native_id != str(EntityId)
            or Entity.id != f"fusion-sketch-entity-{EntityId}"
            or SpanValue is None
            or not SpanValue.IsPrimary
            or KSketchKinds.get(SpanValue.ClassGuid) != KindValue
            or not 0
            <= SpanValue.PayloadOffset + 4
            <= SpanValue.EndOffset - 11
            < len(BulkData)
            or SpanValue.EndOffset > len(BulkData)
        ):
            continue
        Cursor = MetaCursor(BulkData[SpanValue.EndOffset - 11 : SpanValue.EndOffset])
        try:
            NativeOwner = ReadNativeRef(Cursor)
        except ValueError:
            continue
        if NativeOwner != OwnerId:
            continue
        if EntityId in Entities:
            raise ValueError("Ambiguous Fusion sketch relation entity")
        Entities[EntityId] = Entity
    return Entities
