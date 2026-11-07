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

# descriptor support backlinks distinguish owned source picks from orphaned recipes
KSupportGuid = "6CCF41D5-40BE-48ED-A834-18F3EAED6C57"


# the reciprocal support list must explicitly name the historical source named by the anchor
def ReadPickSupport(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SupportId: int,
    DescriptorId: int,
    SourceId: int,
) -> None:
    Cursor = SelectCursor(BulkData, Owners, SupportId, KSupportGuid)
    if Cursor.TakeBytes(6) != bytes(6):
        raise ValueError("Unsupported Fusion topology selection support prefix")
    Flags = Cursor.TakeBytes(2)
    Count = Cursor.ReadCount(2)
    if Count == 0 or Flags != b"\1\1" or len(Cursor.DataValue) != 39 + 19 * Count:
        raise ValueError("Unsupported Fusion topology selection support count")
    Sources = []
    for _ in range(Count):
        Sources.append(ReadNativeRef(Cursor))
        Cursor.TakeBytes(8)
    if (
        SourceId not in Sources
        or any(Identity not in Owners for Identity in Sources)
        or ReadNativeRef(Cursor) != DescriptorId
    ):
        raise ValueError("Fusion topology selection support owner disagrees")
    Cursor.TakeBytes(8)
    if Cursor.TakeBytes(8) != bytes(8):
        raise ValueError("Unsupported Fusion topology selection support suffix")
