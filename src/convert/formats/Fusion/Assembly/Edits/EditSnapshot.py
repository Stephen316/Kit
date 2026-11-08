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
)
from convert.formats.Fusion.Assembly.Edits.EditCreation import (
    KNilNamespace,
    ReadEditCreate,
)
from convert.formats.Fusion.Assembly.Edits.EditState import CheckEditState
from convert.formats.Fusion.Assembly.OccurTransform import ReadOccurMatrix
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadSelectUuid

# only the verified creation subtype of this native feature can be skipped
KEditSnapshot = "54F9ACE8-B5B8-4A6E-B582-64F629511DE4"


# creation snapshot effects are bounded by their datum and typed dependency table
def ReadEditSnap(
    BulkData: bytes,
    IndexValue: AsmEditIndex,
    SnapshotId: int,
    TimelineIds: frozenset[int],
) -> int:
    Cursor = SelectCursor(BulkData, IndexValue.Owners, SnapshotId, KEditSnapshot)
    if Cursor.TakeBytes(6) != bytes(6):
        raise ValueError("Unsupported Fusion component creation snapshot prefix")
    DatumId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Unsupported Fusion component creation snapshot mode")
    Matrix = ReadOccurMatrix(Cursor)
    if (
        ReadSelectUuid(Cursor) != KNilNamespace
        or len(Cursor.DataValue) != Cursor.Offset + 157
    ):
        raise ValueError("Unsupported Fusion component creation snapshot extent")
    if Cursor.TakeBytes(7) != b"\0\0\0\1\0\0\0" or ReadNativeRef(Cursor) != DatumId:
        raise ValueError("Fusion component creation snapshot datum disagrees")
    if Cursor.TakeBytes(8) != b"\xff" * 4 + bytes(4):
        raise ValueError("Unsupported Fusion component creation snapshot label framing")
    StoredIndex = Cursor.ReadLong()
    if (
        StoredIndex > 0xFFFFFFFF
        or Cursor.TakeBytes(4) != bytes(4)
        or Cursor.ReadWord() != 3
        or ReadNativeRef(Cursor) != SnapshotId
    ):
        raise ValueError("Unsupported Fusion component creation snapshot dependencies")
    CreateId = ReadNativeRef(Cursor)
    ScopeId = ReadNativeRef(Cursor)
    if CreateId in TimelineIds:
        raise ValueError(
            "Fusion component creation and snapshot both appear in history"
        )
    ComponentId = ReadEditCreate(
        BulkData, IndexValue, CreateId, ScopeId, SnapshotId, StoredIndex
    )
    Occurrence = ReadEditDatum(BulkData, IndexValue, DatumId, SnapshotId)
    if Occurrence.ComponentId != ComponentId or not HasSameMatrix(
        Matrix, Occurrence.Transform
    ):
        raise ValueError("Fusion creation snapshot and current occurrence disagree")
    CheckEditState(BulkData, IndexValue, Cursor.DataValue, SnapshotId, SnapshotId, True)
    return Occurrence.ObjectId
