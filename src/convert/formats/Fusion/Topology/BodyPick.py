# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite
from struct import unpack as Unpack

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadSelectUuid
from convert.formats.Fusion.Topology.BodyAnchor import KAnchorGuid, ReadBodyAnchor
from convert.formats.Fusion.Topology.BodyPickContext import CheckBodyCtx
from convert.formats.Fusion.Topology.BodyPickSupport import CheckBodySup
from convert.formats.Fusion.Topology.BodyRecipe import ReadBodyRecipe
from convert.formats.Fusion.Topology.PickDescriptor import KPickHelper

# whole body picks use a descriptor distinct from face and edge selections
KBodyDesc = "9716F783-676D-42E0-93F9-EBF273E7C035"


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
def ReadBodyTail(Cursor: MetaCursor, FeatureId: int) -> tuple[int, int]:
    _ = Cursor.TakeBytes(14)
    if Cursor.TakeBytes(4) != b"\1\1\0\0" or not IsFinite(
        Unpack("<d", Cursor.TakeBytes(8))[0]
    ):
        raise ValueError("Unsupported Fusion body pick trailer")
    if Cursor.TakeBytes(4) != b"\1\1\0\0":
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
    BulkData: bytes, Owners: dict[int, RecordSpan], DescriptorId: int, FeatureId: int
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
    ContextIds = tuple(ReadNativeRef(Cursor) for _ in range(Cursor.ReadCount(1)))
    if Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion body pick anchor count")
    AnchorId = ReadNativeRef(Cursor)
    HelperId, SupportId = ReadBodyTail(Cursor, FeatureId)
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
