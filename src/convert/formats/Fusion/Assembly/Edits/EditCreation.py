# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Assembly.Edits.AsmEditIndex import AsmEditIndex
from convert.formats.Fusion.Assembly.ComponentRead import KComponentGuid
from convert.formats.Fusion.Assembly.Edits.EditBookkeep import CheckEditBook
from convert.formats.Fusion.Assembly.Edits.EditState import CheckEditState
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadSelectUuid

# a creation record anchors the placement snapshot to a new local definition
KCreateComp = "78B9DEFC-DA1C-4ED0-A395-40890BDAE590"

# a component scope provides a second typed connection to the same snapshot
KCreateScope = "5D15E992-1E93-4D79-A553-10D2624148AE"

# assembly edit identity text uses the local empty namespace
KNilNamespace = "00000000-0000-0000-0000-000000000000"


# reciprocal creation and scope links delimit a placement only feature
def ReadEditCreate(
    BulkData: bytes,
    IndexValue: AsmEditIndex,
    CreateId: int,
    ScopeId: int,
    SnapshotId: int,
    StoredIndex: int,
) -> int:
    Owners = IndexValue.Owners
    Cursor = SelectCursor(BulkData, Owners, CreateId, KCreateComp)
    if (
        len(Cursor.DataValue) != 222
        or Cursor.TakeBytes(2) != bytes(2)
        or ReadNativeRef(Cursor) != ScopeId
        or ReadSelectUuid(Cursor) != KNilNamespace
        or Cursor.TakeBytes(11) != bytes(7) + b"\xff" * 4
        or Cursor.ReadText(True, Maximum=15) != "CreateComponent"
        or Cursor.ReadLong() != StoredIndex
        or Cursor.ReadText(True, Maximum=0)
    ):
        raise ValueError("Unsupported Fusion component creation framing")
    CheckEditState(BulkData, IndexValue, Cursor.DataValue, CreateId, SnapshotId, False)
    Scope = SelectCursor(BulkData, Owners, ScopeId, KCreateScope)
    if len(Scope.DataValue) != 40 or Scope.TakeBytes(3) != b"\0\0\1":
        raise ValueError("Unsupported Fusion component creation scope")
    ComponentId = ReadNativeRef(Scope)
    if Scope.TakeBytes(3) != b"\1\0\0":
        raise ValueError("Unsupported Fusion component creation scope marker")
    BookId = ReadNativeRef(Scope)
    if ReadNativeRef(Scope) != SnapshotId or Scope.TakeBytes(1) != bytes(1):
        raise ValueError("Fusion component creation scope snapshot disagrees")
    _ = SelectCursor(BulkData, Owners, ComponentId, KComponentGuid)
    CheckEditBook(BulkData, IndexValue, BookId, ScopeId, 0)
    return ComponentId
