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
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaCtx import ReadMetaCtx
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
    Header = ReadWireHead(Cursor, Segment)
    Classes = ReadWireClasses(Cursor)
    StoredIds = tuple(Cursor.ReadLong() for _ in range(Cursor.ReadCount(KMaxMetaIds)))
    Primary, Continued = ReadWireTable(Cursor), ReadWireTable(Cursor)
    NextId, Reserved = Cursor.ReadLong(), Cursor.ReadWord()
    Contexts = ReadMetaCtx(Cursor, Reserved)
    Value = MetaSegment(
        Header,
        Classes,
        StoredIds,
        Primary,
        Continued,
        NextId,
        Reserved,
        tuple(
            MetaProperty(Cursor.ReadText(), Cursor.ReadWord())
            for _ in range(Cursor.ReadCount(KMaxMetaProps))
        ),
        Contexts,
    )
    if Cursor.Offset != len(DataValue):
        raise ValueError("Trailing Fusion MetaStream data")
    CheckWireBody(Value)
    return Value
