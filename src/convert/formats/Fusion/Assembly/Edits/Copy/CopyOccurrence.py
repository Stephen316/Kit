# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.Edits.AsmEditIndex import AsmEditIndex
from convert.formats.Fusion.Assembly.Edits.AsmEditOccur import (
    HasSameMatrix,
    ReadEditDatum,
    ReadEditOccur,
)
from convert.formats.Fusion.Assembly.Edits.Copy.CopyFrame import ReadCopyFrame
from convert.formats.Fusion.Assembly.Edits.Copy.CopyLinks import ReadCopyLinks
from convert.formats.Fusion.Assembly.Edits.EditCreation import KNilNamespace
from convert.formats.Fusion.Assembly.Edits.EditState import CheckEditState
from convert.formats.Fusion.Assembly.OccurTransform import ReadOccurMatrix
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadSelectUuid

# only the separately verified local occurrence subtype of copy paste is admitted
KCopyOccurrence = "D57B1A22-9D5A-4D7D-A909-E08C579612CA"


# copy caches corroborate the recorded source and target transforms without solving any motion
def MultiplyCopy(
    First: tuple[float, ...], Second: tuple[float, ...]
) -> tuple[float, ...]:
    return tuple(
        sum(
            First[RowIndex * 4 + Inner] * Second[Inner * 4 + Column]
            for Inner in range(4)
        )
        for RowIndex in range(4)
        for Column in range(4)
    )


# a verified source creation and two matching contexts prove a repeated local instance
def ReadEditCopy(
    BulkData: bytes,
    IndexValue: AsmEditIndex,
    FeatureId: int,
    Snapshots: dict[int, int],
) -> int:
    Cursor = SelectCursor(BulkData, IndexValue.Owners, FeatureId, KCopyOccurrence)
    if len(Cursor.DataValue) != 507 or Cursor.TakeBytes(3) != bytes(3):
        raise ValueError("Unsupported Fusion copy feature framing")
    SourceFrameId = ReadNativeRef(Cursor)
    if Cursor.DataValue[Cursor.Offset : Cursor.Offset + 1] != bytes(1):
        raise ValueError("Unsupported Fusion copy relative matrix")
    Relative = ReadOccurMatrix(Cursor)
    TargetFrameId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(4) != bytes(4):
        raise ValueError("Unsupported Fusion copy datum marker")
    DatumId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != b"\1" or Cursor.DataValue[
        Cursor.Offset : Cursor.Offset + 1
    ] != bytes(1):
        raise ValueError("Unsupported Fusion copy result matrix")
    Result = ReadOccurMatrix(Cursor)
    if (
        ReadSelectUuid(Cursor) != KNilNamespace
        or Cursor.TakeBytes(7) != b"\0\0\0\1\0\0\0"
        or ReadNativeRef(Cursor) != DatumId
        or Cursor.TakeBytes(4) != b"\xff" * 4
        or Cursor.ReadText(True, Maximum=9) != "CopyPaste"
        or Cursor.ReadLong() > 0xFFFFFFFF
        or Cursor.ReadText(True, Maximum=0)
        or Cursor.Offset != len(Cursor.DataValue) - 76
    ):
        raise ValueError("Fusion copy repeated result datum or label disagrees")
    SourceLink, SourceMatrix, SourceGuid, SourceTerminal = ReadCopyFrame(
        BulkData, IndexValue, SourceFrameId, FeatureId, True
    )
    TargetLink, _, _, TargetTerminal = ReadCopyFrame(
        BulkData, IndexValue, TargetFrameId, FeatureId, False
    )
    if SourceTerminal != TargetTerminal:
        raise ValueError("Fusion copy contexts disagree on their terminal route")
    ParentId, SourceSnapshot = ReadCopyLinks(
        BulkData, IndexValue, SourceLink, TargetLink, SourceMatrix
    )
    SourceId = Snapshots.get(SourceSnapshot)
    if SourceId is None:
        raise ValueError("Fusion copy source has no earlier verified creation snapshot")
    Source = ReadEditOccur(BulkData, IndexValue, SourceId)
    Target = ReadEditDatum(BulkData, IndexValue, DatumId, FeatureId)
    Instance = IndexValue.Occurrences[Target.ObjectId]
    if (
        SourceGuid.casefold() != Source.NativeGuid.casefold()
        or Source.ObjectId == Target.ObjectId
        or Source.ComponentId != Target.ComponentId
        or Source.CollectionId != Target.CollectionId
        or ParentId != IndexValue.Components[Instance.owner_definition_id]
        or not HasSameMatrix(SourceMatrix, Source.Transform)
        or not HasSameMatrix(Result, Target.Transform)
        or not HasSameMatrix(MultiplyCopy(SourceMatrix, Relative), Result)
    ):
        raise ValueError("Fusion copy source and created occurrence evidence disagrees")
    CheckEditState(BulkData, IndexValue, Cursor.DataValue, FeatureId, None, True)
    return Target.ObjectId
