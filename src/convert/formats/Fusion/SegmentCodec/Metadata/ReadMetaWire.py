# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Metadata.CheckWireBody import CheckWireBody
from convert.formats.Fusion.SegmentCodec.Metadata.MetaLimits import (
    KMaxMetaIds,
    KMaxMetaProps,
    KMaxMetaSize,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaProperty
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadWireHead import ReadWireHead
from convert.formats.Fusion.SegmentCodec.Metadata.ReadWireRows import (
    ReadWireClasses,
    ReadWireTable,
)


# decoding retains wire order and opaque values without changing the ordinary index path
def ReadMetaWire(
    DataValue: bytes, *, Segment: SegmentKind | None = None
) -> MetaSegment:
    if type(DataValue) is not bytes or len(DataValue) > KMaxMetaSize:
        raise ValueError("Invalid or oversized Fusion MetaStream")
    Cursor = MetaCursor(DataValue)
    Value = MetaSegment(
        ReadWireHead(Cursor, Segment),
        ReadWireClasses(Cursor),
        tuple(Cursor.ReadLong() for Index in range(Cursor.ReadCount(KMaxMetaIds))),
        ReadWireTable(Cursor),
        ReadWireTable(Cursor),
        Cursor.ReadLong(),
        Cursor.ReadWord(),
        tuple(
            MetaProperty(Cursor.ReadText(), Cursor.ReadWord())
            for Index in range(Cursor.ReadCount(KMaxMetaProps))
        ),
    )
    if Cursor.Offset != len(DataValue):
        raise ValueError("Trailing Fusion MetaStream data")
    CheckWireBody(Value)
    return Value
