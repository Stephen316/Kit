# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.Solids.CreatorScopes import (
    CreatorScope,
    KScopeOwner,
    KScopeSnapshot,
)
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor


# creation bookkeeping names the parent scope used when the occurrence was placed
def ReadSnapParent(
    BulkData: bytes, Owners: dict[int, RecordSpan], Scope: CreatorScope
) -> int:
    if Scope.SnapshotId is None:
        raise ValueError("Fusion authoring scope has no creation snapshot")
    Snapshot = SelectCursor(BulkData, Owners, Scope.SnapshotId, KScopeSnapshot)
    Snapshot.Offset = len(Snapshot.DataValue) - 23
    Book = SelectCursor(BulkData, Owners, ReadNativeRef(Snapshot), KScopeOwner)
    if len(Book.DataValue) != 96 or Book.TakeBytes(12) != bytes.fromhex(
        "000000000000010103000000"
    ):
        raise ValueError("Unsupported Fusion creation scope bookkeeping")
    Parent = ReadNativeRef(Book)
    Book.TakeBytes(8)
    if ReadNativeRef(Book) != Scope.ScopeId:
        raise ValueError("Fusion creation snapshot own scope disagrees")
    Book.TakeBytes(8)
    if ReadNativeRef(Book) != Scope.SnapshotId:
        raise ValueError("Fusion creation scope snapshot reference disagrees")
    Stamp = Book.TakeBytes(8)
    if ReadNativeRef(Book) != Scope.SnapshotId or Book.TakeBytes(8) != Stamp:
        raise ValueError("Fusion creation scope repeated snapshot disagrees")
    if Book.TakeBytes(8) != bytes(8):
        raise ValueError("Unsupported Fusion creation scope bookkeeping suffix")
    return Parent
