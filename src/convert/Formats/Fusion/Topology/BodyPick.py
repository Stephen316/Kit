from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite
from struct import unpack as Unpack

from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.SelectionRef import ReadSelectUuid
from convert.Formats.Fusion.Topology.BodyAnchor import KAnchorGuid, ReadBodyAnchor
from convert.Formats.Fusion.Topology.BodyPickContext import CheckBodyCtx
from convert.Formats.Fusion.Topology.BodyPickSupport import CheckBodySup
from convert.Formats.Fusion.Topology.BodyRecipe import ReadBodyRecipe
from convert.Formats.Fusion.Topology.PickDescriptor import KPickHelper

# whole body picks use a descriptor distinct from face and edge selections
KBodyDesc = "9716F783-676D-42E0-93F9-EBF273E7C035"

# the witnessed cut target uses this mode in both the proxy and descriptor
KCutTargetMode = 8

# the extent field has its own descriptor mode with a required root context
KCutEndMode = 9

# the cut target mode uses distinct markers from the ordinary body pick
KCutPickMarker = b"\4\1\0\0"


# the verified pick identifies a historical body without asserting current lifecycle
@MakeDataClass(frozen=True, slots=True)
class BodyPick:
    DescriptorId: int
    BodyId: int
    AnchorId: int
    SourceId: int
    RecipeId: int
    ContextIds: tuple[int, ...]
    HelperId: int
    SupportId: int
    Namespace: str
    EntityGuid: str
    AnchorGuid: str
    RecipeName: str


# the tail holds explicit helper and support links followed by the owning feature
def ReadBodyTail(
    Cursor: MetaCursor,
    FeatureId: int,
    CutTarget: bool,
    CutEnding: bool,
    ContextCount: int,
) -> tuple[int, int]:
    if CutEnding and (CutTarget or ContextCount != 1):
        raise ValueError("Fusion Cut extent descriptor requires its own root context")
    CutMode = KCutEndMode if CutEnding else KCutTargetMode if CutTarget else None
    Header = Cursor.TakeBytes(14)
    Marker = KCutPickMarker if CutMode is not None else b"\1\1\0\0"
    if CutMode is not None and Header != bytes((CutMode,)) + bytes(13):
        raise ValueError("Unsupported Fusion Cut body pick mode")
    if Cursor.TakeBytes(4) != Marker or not IsFinite(
        Unpack("<d", Cursor.TakeBytes(8))[0]
    ):
        raise ValueError("Unsupported Fusion body pick trailer")
    if Cursor.TakeBytes(4) != Marker:
        raise ValueError("Unsupported Fusion body pick helper marker")
    HelperId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(3) != b"\1\0\0":
        raise ValueError("Unsupported Fusion body pick support marker")
    SupportId = ReadNativeRef(Cursor)
    if (
        Cursor.TakeBytes(1) != b"\0"
        or ReadNativeRef(Cursor) != FeatureId
        or Cursor.Offset != len(Cursor.DataValue)
    ):
        raise ValueError("Fusion body pick descriptor owner disagrees")
    return HelperId, SupportId


# typed descriptor and support references must agree with the native body anchor
def ReadBodyPick(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    DescriptorId: int,
    FeatureId: int,
    *,
    CutTarget: bool = False,
    CutEnding: bool = False,
) -> BodyPick:
    Cursor = SelectCursor(BulkData, Owners, DescriptorId, KBodyDesc)
    if (
        len(Cursor.DataValue) not in (279, 290)
        or Cursor.TakeBytes(6) != b"\0\0\1\0\0\0"
    ):
        raise ValueError("Unsupported Fusion body pick prefix")
    _ = Cursor.ReadLong()
    if Cursor.ReadWord() != 33:
        raise ValueError("Unsupported Fusion body pick kind")
    RecipeId = ReadNativeRef(Cursor)
    if Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion body pick namespace count")
    Namespace, EntityGuid = ReadSelectUuid(Cursor), ReadSelectUuid(Cursor)
    if Cursor.ReadLong() != 2:
        raise ValueError("Unsupported Fusion body pick association header")
    ContextIds = tuple(
        ReadNativeRef(Cursor) for _ in range(Cursor.ReadCount(0 if CutTarget else 1))
    )
    if Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion body pick anchor count")
    AnchorId = ReadNativeRef(Cursor)
    HelperId, SupportId = ReadBodyTail(
        Cursor, FeatureId, CutTarget, CutEnding, len(ContextIds)
    )
    Helper = SelectCursor(BulkData, Owners, HelperId, KPickHelper)
    if Helper.DataValue != b"\0\1" + bytes(12):
        raise ValueError("Unsupported Fusion body pick helper")
    BodyId, SourceId = ReadBodyAnchor(BulkData, Owners, AnchorId)
    for ContextId in ContextIds:
        CheckBodyCtx(BulkData, Owners, ContextId, Namespace, EntityGuid, BodyId)
    Anchor = SelectCursor(BulkData, Owners, AnchorId, KAnchorGuid)
    _ = Anchor.TakeBytes(2)
    AnchorGuid = ReadSelectUuid(Anchor)
    CheckBodySup(BulkData, Owners, SupportId, DescriptorId, SourceId, AnchorGuid)
    RecipeName = ReadBodyRecipe(BulkData, Owners, RecipeId)
    return BodyPick(
        DescriptorId,
        BodyId,
        AnchorId,
        SourceId,
        RecipeId,
        ContextIds,
        HelperId,
        SupportId,
        Namespace,
        EntityGuid,
        AnchorGuid,
        RecipeName,
    )
