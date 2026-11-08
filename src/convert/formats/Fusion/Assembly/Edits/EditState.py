# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite
from struct import unpack as Unpack

from convert.formats.Fusion.Assembly.Edits.AsmEditIndex import AsmEditIndex
from convert.formats.Fusion.Assembly.Edits.EditBookkeep import CheckEditBook
from convert.formats.Fusion.Assembly.Edits.EditSupport import CheckEditSup
from convert.formats.Fusion.HistoryRef import ReadNativeRef, ReadOptionalRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SelectionProxy import SelectCursor

# these footer records validate shared state without treating a placement as solved
KOptionalSup = "074F9459-89C2-4B7D-8AB4-DCE67AE944FE"

# the fixed helper anchors the repeated saved suppression and rollback flags
KStateHelper = "5FBE538E-139B-46D4-BCAF-CC796D1E1F78"


# both copies of saved state must prove an active occurrence edit
def CheckEditState(
    BulkData: bytes,
    IndexValue: AsmEditIndex,
    BodyValue: bytes,
    OwnerId: int,
    RelatedId: int | None,
    HasSupport: bool,
) -> None:
    Width = 66 + 10 * int(RelatedId is not None) + 10 * int(HasSupport)
    Cursor = MetaCursor(BodyValue[-Width:])
    if Cursor.TakeBytes(7) != bytes(7):
        raise ValueError("Inactive or unsupported Fusion assembly edit state")
    CheckEditSup(BulkData, IndexValue, ReadNativeRef(Cursor))
    OptionalId = ReadOptionalRef(Cursor)
    if (OptionalId is not None) != HasSupport:
        raise ValueError("Fusion assembly edit optional support disagrees")
    Owners = IndexValue.Owners
    if OptionalId is not None:
        Support = SelectCursor(BulkData, Owners, OptionalId, KOptionalSup)
        if Support.DataValue != bytes(2) + b"\1\1" + bytes(13):
            raise ValueError("Unsupported Fusion assembly edit optional support")
    if Cursor.TakeBytes(8) != b"\xff" * 4 + b"\1\1\0\0":
        raise ValueError("Unsupported Fusion assembly edit state framing")
    if (
        not IsFinite(Unpack("<d", Cursor.TakeBytes(8))[0])
        or Cursor.TakeBytes(4) != b"\1\1\0\0"
    ):
        raise ValueError("Unsupported Fusion assembly edit state scalar")
    Helper = SelectCursor(BulkData, Owners, ReadNativeRef(Cursor), KStateHelper)
    if Helper.DataValue != b"\0\1" + bytes(12) or Cursor.TakeBytes(3) != b"\1\0\0":
        raise ValueError("Unsupported Fusion assembly edit helper or flags")
    CheckEditBook(BulkData, IndexValue, ReadNativeRef(Cursor), OwnerId)
    if (
        ReadOptionalRef(Cursor) != RelatedId
        or Cursor.TakeBytes(1) != bytes(1)
        or Cursor.Offset != len(Cursor.DataValue)
    ):
        raise ValueError("Fusion assembly edit state relation disagrees")
