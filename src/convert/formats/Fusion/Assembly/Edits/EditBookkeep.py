# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.Edits.AsmEditIndex import AsmEditIndex
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.SelectionProxy import SelectCursor

# shared bookkeeping contains counted links and one independent owner backlink
KEditBookkeep = "6CCF41D5-40BE-48ED-A834-18F3EAED6C57"


# metadata bookkeeping keeps the owning edit distinct from its historical references
def CheckEditBook(
    BulkData: bytes,
    IndexValue: AsmEditIndex,
    BookId: int,
    OwnerId: int,
    ExpectedCount: int | None = None,
) -> None:
    Owners = IndexValue.Owners
    Cursor = SelectCursor(BulkData, Owners, BookId, KEditBookkeep)
    if Cursor.TakeBytes(6) != bytes(6) or any(
        FlagValue not in (0, 1) for FlagValue in Cursor.TakeBytes(2)
    ):
        raise ValueError("Unsupported Fusion assembly edit bookkeeping header")
    Count = Cursor.ReadCount(100000)
    if len(Cursor.DataValue) != 39 + 19 * Count or (
        ExpectedCount is not None and Count != ExpectedCount
    ):
        raise ValueError("Unsupported Fusion assembly edit bookkeeping count")
    for _ in range(Count):
        if ReadNativeRef(Cursor) not in Owners:
            raise ValueError("Unknown Fusion assembly edit bookkeeping member")
        Cursor.ReadLong()
    if ReadNativeRef(Cursor) != OwnerId:
        raise ValueError("Fusion assembly edit bookkeeping owner disagrees")
    Cursor.ReadLong()
    if Cursor.TakeBytes(8) != bytes(8):
        raise ValueError("Unsupported Fusion assembly edit bookkeeping suffix")
