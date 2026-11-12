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
        tuple(Cursor.ReadLong() for _ in range(Cursor.ReadCount(KMaxMetaIds))),
        ReadWireTable(Cursor),
        ReadWireTable(Cursor),
        Cursor.ReadLong(),
        Cursor.ReadWord(),
        tuple(
            MetaProperty(Cursor.ReadText(), Cursor.ReadWord())
            for _ in range(Cursor.ReadCount(KMaxMetaProps))
        ),
    )
    if Cursor.Offset != len(DataValue):
        raise ValueError("Trailing Fusion MetaStream data")
    CheckWireBody(Value)
    return Value
