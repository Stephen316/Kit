# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


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
    _ = ReadSelectUuid(Cursor)
    if any(FlagValue not in (0, 1) for FlagValue in Cursor.TakeBytes(2)):
        raise ValueError("Unsupported Fusion body anchor flags")
    BodyId = ReadNativeRef(Cursor)
    SourceId = ReadNativeRef(Cursor)
    _ = SelectCursor(BulkData, Owners, BodyId, KBodyGuid)
    if SourceId not in Owners:
        raise ValueError("Missing Fusion body anchor source")
    return BodyId, SourceId
