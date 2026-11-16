from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite
from struct import unpack as Unpack

from convert.Formats.Fusion.Extrudes.Plane.PlanePickSupport import KSketchFaceMode
from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.SelectionRef import ReadSelectUuid
from convert.Formats.Fusion.Topology.BodyPick import KCutPickMarker
from convert.Formats.Fusion.Topology.PickDescriptor import KPickHelper, KTopoSelect


# an unresolved face attachment still needs a typed reproducible source recipe
@MakeDataClass(frozen=True, slots=True)
class FaceDescriptor:
    RecipeId: int
    ContextIds: tuple[int, ...]
    AnchorId: int
    SupportId: int
    Namespace: str
    EntityGuid: str


# the exact four context trailer distinguishes a sketch support from an ordinary face pick
def ReadFaceTailMut(Cursor: MetaCursor, FeatureId: int) -> tuple[int, int]:
    if (
        (Cursor.ReadWord(), Cursor.ReadWord()) != (KSketchFaceMode, 4)
        or Cursor.TakeBytes(6) != bytes(6)
        or Cursor.TakeBytes(4) != KCutPickMarker
        or not IsFinite(Unpack("<d", Cursor.TakeBytes(8))[0])
        or Cursor.TakeBytes(4) != KCutPickMarker
    ):
        raise ValueError("Unsupported Fusion sketch face support trailer")
    HelperId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(3) != b"\1\0\0":
        raise ValueError("Unsupported Fusion sketch face support helper")
    SupportId = ReadNativeRef(Cursor)
    if (
        Cursor.TakeBytes(1) != bytes(1)
        or ReadNativeRef(Cursor) != FeatureId
        or Cursor.Offset != len(Cursor.DataValue)
    ):
        raise ValueError("Fusion sketch face support owner disagrees")
    return HelperId, SupportId


# the descriptor must name the complete scoped boundary before exposing a face recipe
def ReadFaceDesc(
    BulkData: bytes, Owners: dict[int, RecordSpan], DescriptorId: int, FeatureId: int
) -> FaceDescriptor:
    Cursor = SelectCursor(BulkData, Owners, DescriptorId, KTopoSelect)
    if len(Cursor.DataValue) != 309 or Cursor.TakeBytes(4) != bytes(4):
        raise ValueError("Unsupported Fusion sketch face support descriptor")
    RecipeId = ReadNativeRef(Cursor)
    if Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion sketch face support namespace count")
    Namespace, EntityGuid = ReadSelectUuid(Cursor), ReadSelectUuid(Cursor)
    if Cursor.ReadLong() != 2 or Cursor.ReadWord() != 4:
        raise ValueError("Unsupported Fusion sketch face support context count")
    ContextIds = tuple(ReadNativeRef(Cursor) for _ in range(4))
    if len(set(ContextIds)) != 4 or Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion sketch face support anchor or context")
    AnchorId = ReadNativeRef(Cursor)
    HelperId, SupportId = ReadFaceTailMut(Cursor, FeatureId)
    Helper = SelectCursor(BulkData, Owners, HelperId, KPickHelper)
    if Helper.DataValue != b"\0\1" + bytes(12):
        raise ValueError("Unsupported Fusion sketch face support helper payload")
    return FaceDescriptor(
        RecipeId, ContextIds, AnchorId, SupportId, Namespace, EntityGuid
    )
