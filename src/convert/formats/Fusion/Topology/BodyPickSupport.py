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
from convert.formats.Fusion.Topology.PickSupport import KSupportGuid


# the whole body support corroborates the anchor namespace and receiver independently
def CheckBodySup(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SupportId: int,
    DescriptorId: int,
    SourceId: int,
    AnchorGuid: str,
) -> None:
    Cursor = SelectCursor(BulkData, Owners, SupportId, KSupportGuid)
    if Cursor.TakeBytes(6) != b"\0\0\1\0\0\0" or ReadSelectUuid(Cursor) != AnchorGuid:
        raise ValueError("Fusion body pick support and anchor disagree")
    Cursor.TakeBytes(8)
    Flags = Cursor.TakeBytes(2)
    Count = Cursor.ReadCount(1024)
    if (
        any(Value not in (0, 1) for Value in Flags)
        or not Count
        or (len(Cursor.DataValue) - Cursor.Offset != 19 * Count + 27)
    ):
        raise ValueError("Unsupported Fusion body pick support layout")
    SourceIds = []
    for _ in range(Count):
        SourceIds.append(ReadNativeRef(Cursor))
        Cursor.TakeBytes(8)
    if (
        SourceId not in SourceIds
        or len(set(SourceIds)) != Count
        or any(Identity not in Owners for Identity in SourceIds)
        or ReadNativeRef(Cursor) != DescriptorId
    ):
        raise ValueError("Fusion body pick support ownership disagrees")
    Cursor.TakeBytes(8)
    if Cursor.TakeBytes(8) != bytes(8):
        raise ValueError("Unsupported Fusion body pick support suffix")
