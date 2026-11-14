from dataclasses import replace as ReplaceValue
from struct import pack as PackValue

from pytest import raises as Raises

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.MetaIndex import (
    CheckMetaHeader,
    KSegmentLayout,
    ReadMetaIndex,
    SegmentKind,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaContext import MetaContext
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import (
    MetaClass,
    MetaOffset,
    MetaProperty,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from convert.formats.Fusion.SegmentCodec.Metadata.WriteMetaWire import WriteMetaWire


# synthetic rows separate registry and table order from physical record ordering
def MakeMetaModel(Segment: SegmentKind) -> MetaSegment:
    SegmentId, Storage = KSegmentLayout[Segment]
    return MetaSegment(
        MetaHeader(
            Segment,
            17 if SegmentId is None else SegmentId,
            "scope 🧭",
            1234,
            8,
            (33, 0xDEADBEEF),
            Segment.value,
            "testspace",
            Storage,
        ),
        (
            MetaClass("NodeOwner", "NodeBases", 0xAABBCCDD, "Shape", (41, 9)),
            MetaClass("NodeBases", "", 3, "Base", (7,)),
        ),
        (7, 41, 9),
        (MetaOffset(9, 30), MetaOffset(41, 0), MetaOffset(7, 45)),
        (MetaOffset(41, 15),),
        90,
        1,
        (MetaProperty("Zeta", 7), MetaProperty("Alpha", 10)),
        (
            MetaContext(
                (1 << 63) + 0x76543210,
                "7a654321-1111-4222-8333-abcdef654321",
                "7d654321-1111-4222-8333-abcdef654321",
                "urn:adsk.wipprod:fs.file:vf.SyntheticMetaKey000?version=2",
                "7c654321-1111-4222-8333-abcdef654321",
                0,
            ),
        ),
    )


# native readers accept newly constructed metadata and its explicitly indexed bulk records
def TestMetaEmit() -> None:
    BulkData = b"".join(
        PackValue("<I3sQ", 3, CodeValue, Identity)
        for CodeValue, Identity in (
            (b"256", 41),
            (b"257", 41),
            (b"256", 9),
            (b"257", 7),
        )
    )
    for Segment in SegmentKind:
        Value = MakeMetaModel(Segment)
        DataValue = WriteMetaWire(Value)
        assert (
            ReadMetaWire(DataValue) == ReadMetaWire(DataValue, Segment=Segment) == Value
        )
        assert WriteMetaWire(ReadMetaWire(DataValue)) == DataValue
        Classes, Owners, Entries = ReadMetaIndex(DataValue, Segment=Segment)
        assert tuple(Classes.items()) == (
            (256, ("NodeOwner", "NodeBases", "Shape")),
            (257, ("NodeBases", "", "Base")),
        )
        assert tuple(Owners.items()) == ((41, 256), (9, 256), (7, 257))
        assert Entries == [(30, 9, True), (0, 41, True), (45, 7, True), (15, 41, False)]
        Spans = ReadBulkSpans(BulkData, DataValue, Segment=Segment)
        assert tuple(
            (Entry.ObjectId, Entry.TypeCode, Entry.IsPrimary) for Entry in Spans
        ) == (
            (41, 256, True),
            (41, 257, False),
            (9, 256, True),
            (7, 257, True),
        )


# opaque stored identity values retain their wire ordering without implied topology rules
def TestStoredIds() -> None:
    Value = ReplaceValue(MakeMetaModel(SegmentKind.KDesign), StoredIds=(41, 1000, 41))
    assert ReadMetaWire(WriteMetaWire(Value)) == Value


# malformed framing and registry relations fail before typed rows leave the decoder
def TestMetaReadBad() -> None:
    Segment = SegmentKind.KDesign
    DataValue = WriteMetaWire(MakeMetaModel(Segment))
    Cursor = MetaCursor(DataValue)
    CheckMetaHeader(Cursor, Segment)
    Start = Cursor.Offset
    BadCount = DataValue[:Start] + PackValue("<I", 100001) + DataValue[Start + 4 :]
    BadClass = DataValue.replace(b"NodeOwner", b"NodeBases", 1)
    BadOffset = DataValue.replace(PackValue("<QQ", 41, 15), PackValue("<QQ", 41, 30), 1)
    for Entry in (b"", DataValue[:-1], DataValue + b"x", BadCount, BadClass, BadOffset):
        with Raises(ValueError):
            _ = ReadMetaWire(Entry)
    with Raises(ValueError, match="segment kind"):
        _ = ReadMetaWire(DataValue, Segment=SegmentKind.KAct)


# invalid model fields cannot reach binary output through the typed emitter
def TestMetaEmitBad() -> None:
    Value = MakeMetaModel(SegmentKind.KAct)
    Header = Value.Header
    for Invalid in (
        ReplaceValue(Value, Header=ReplaceValue(Header, SegmentId=0)),
        ReplaceValue(Value, Header=ReplaceValue(Header, Version=9)),
        ReplaceValue(Value, Header=ReplaceValue(Header, Namespace="🧭" * 2049)),
        ReplaceValue(Value, Header=ReplaceValue(Header, StorageSpace="bad\x00")),
        ReplaceValue(Value, Classes=(Value.Classes[0], Value.Classes[0])),
        ReplaceValue(Value, Primary=(MetaOffset(7, 0), MetaOffset(7, 30))),
        ReplaceValue(Value, Continuations=(MetaOffset(8, 15),)),
        ReplaceValue(Value, Continuations=(MetaOffset(41, 30),)),
        ReplaceValue(Value, NextId=41),
        ReplaceValue(Value, NextId=1 << 64),
        ReplaceValue(Value, Reserved=-1),
        ReplaceValue(Value, Properties=(MetaProperty("Alpha", True),)),
        ReplaceValue(Value, Properties=(MetaProperty("Alpha", 1),) * 1025),
        ReplaceValue(
            Value, Properties=(MetaProperty("Alpha", 1), MetaProperty("Alpha", 2))
        ),
    ):
        with Raises(ValueError):
            _ = WriteMetaWire(Invalid)
