# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadSelectUuid

# an anchor addresses the historical native body and its source feature
KAnchorGuid = "D26351F0-5940-4D23-AA20-2C35475A6D9E"

# the target of a body anchor must be a native body rather than a matching number
KBodyGuid = "D3937028-C20C-4E65-B010-94AD418A5C20"


# bounded native references establish the body identity and source feature separately
def ReadBodyAnchor(
    BulkData: bytes, Owners: dict[int, RecordSpan], AnchorId: int
) -> tuple[int, int]:
    Cursor = SelectCursor(BulkData, Owners, AnchorId, KAnchorGuid)
    if len(Cursor.DataValue) != 102 or Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion body anchor layout")
    ReadSelectUuid(Cursor)
    if any(Flag not in (0, 1) for Flag in Cursor.TakeBytes(2)):
        raise ValueError("Unsupported Fusion body anchor flags")
    BodyId = ReadNativeRef(Cursor)
    SourceId = ReadNativeRef(Cursor)
    SelectCursor(BulkData, Owners, BodyId, KBodyGuid)
    if SourceId not in Owners:
        raise ValueError("Missing Fusion body anchor source")
    return BodyId, SourceId
