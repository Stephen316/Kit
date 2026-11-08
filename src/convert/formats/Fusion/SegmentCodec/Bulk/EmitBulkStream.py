# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Iterable

from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMaxBulkBytes
from convert.formats.Fusion.SegmentCodec.Bulk.BulkOwners import BulkOwners
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Bulk.EmitBulkHeader import EmitBulkHeader


# metadata offsets must come from the bytes actually emitted for each native record
def EmitBulkStream(
    Records: Iterable[BulkRecord], *, MaxBytes: int = KMaxBulkBytes
) -> tuple[bytes, tuple[tuple[int, int, bool], ...]]:
    if type(MaxBytes) is not int or not 0 < MaxBytes <= KMaxBulkBytes:
        raise ValueError("Invalid Fusion BulkStream size limit")
    Output = bytearray()
    Entries: list[tuple[int, int, bool]] = []
    Owners = BulkOwners()
    for RecordValue in Records:
        if (
            not isinstance(RecordValue, BulkRecord)
            or type(RecordValue.IsPrimary) is not bool
            or type(RecordValue.Payload) is not bytes
        ):
            raise ValueError("Invalid Fusion BulkStream record")
        Header = EmitBulkHeader(RecordValue.TypeCode, RecordValue.ObjectId)
        Offset = len(Output)
        if Offset + len(Header) + len(RecordValue.Payload) > MaxBytes:
            raise ValueError("Fusion BulkStream size exceeds limit")
        Owners.AddRecord(RecordValue)
        Entries.append((Offset, RecordValue.ObjectId, RecordValue.IsPrimary))
        Output.extend(Header)
        Output.extend(RecordValue.Payload)
    Owners.CheckComplete()
    return bytes(Output), tuple(Entries)
