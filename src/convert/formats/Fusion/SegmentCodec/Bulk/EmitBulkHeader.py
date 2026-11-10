# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import (
    KMaxClassCode,
    KMaxWireId,
    KMinClassCode,
)


# generated framing derives canonical decimal class tokens from validated identifiers
def EmitBulkHeader(TypeCode: int, ObjectId: int) -> bytes:
    if type(TypeCode) is not int or not KMinClassCode <= TypeCode <= KMaxClassCode:
        raise ValueError("Fusion BulkStream class code is outside the registry range")
    if type(ObjectId) is not int or not 0 <= ObjectId <= KMaxWireId:
        raise ValueError("Fusion BulkStream identity is outside the unsigned range")
    TypeText = str(TypeCode).encode("ascii")
    return PackValue("<I", len(TypeText)) + TypeText + PackValue("<Q", ObjectId)
