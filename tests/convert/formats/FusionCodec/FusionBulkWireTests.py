from pathlib import Path as FilePath
from struct import pack as PackValue
from typing import cast as CastValue
from zipfile import ZipFile

from pytest import MonkeyPatch as PatchContext
from pytest import mark as TestMarks, raises as Raises, skip as SkipCase

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.ContainerCodec.ContainerLayout import KCoreSegments
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import (
    KMaxBulkBytes,
    KMaxClassCode,
    KMaxWireId,
)
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Bulk.EmitBulkHeader import EmitBulkHeader
from convert.formats.Fusion.SegmentCodec.Bulk.EmitBulkStream import EmitBulkStream
from tests.convert.formats.FusionIndexTests import IndexFixture

# controlled captures cover one native pair for each of the three segment kinds
KFixtureRoot = "re/Fusion/Study/planedefinitions-6cd0820a832e"


# metadata must be able to index a complete new stream without any captured payload
def TestBulkRound() -> None:
    Records = (BulkRecord(257, 42, True, b"x"), BulkRecord(256, 42, False, b""))
    Payload, Entries = EmitBulkStream(iter(Records))
    assert Entries == ((0, 42, True), (16, 42, False))
    assert Payload == PackValue("<I3sQ", 3, b"257", 42) + b"x" + PackValue(
        "<I3sQ", 3, b"256", 42
    )
    assert ReadBulkSpans(Payload, IndexFixture(Entries[1][0])) == (
        RecordSpan(0, 15, 16, 42, 257, "Child", "", True),
        RecordSpan(16, 31, 31, 42, 256, "Base", "", False),
    )


# valid storage order and repeated continuations must remain independent of ownership
def TestBulkOrder() -> None:
    Payload, Entries = EmitBulkStream(
        (
            BulkRecord(256, 0, False, b"one"),
            BulkRecord(257, 0, True, b""),
            BulkRecord(256, 0, False, b"two"),
        )
    )
    assert Entries == ((0, 0, False), (18, 0, True), (33, 0, False))
    assert Payload == (
        PackValue("<I3sQ", 3, b"256", 0)
        + b"one"
        + PackValue("<I3sQ", 3, b"257", 0)
        + PackValue("<I3sQ", 3, b"256", 0)
        + b"two"
    )


# the native header needs the complete identity width and canonical class digits
def TestBulkHeader() -> None:
    assert EmitBulkHeader(256, 0) == PackValue("<I3sQ", 3, b"256", 0)
    assert EmitBulkHeader(KMaxClassCode, KMaxWireId) == PackValue(
        "<I6sQ", 6, b"100255", KMaxWireId
    )


# negative signed booleans and preformatted labels must fail before native encoding
@TestMarks.parametrize(
    ("TypeCode", "ObjectId"),
    (
        (255, 0),
        (KMaxClassCode + 1, 0),
        ("0256", 0),
        (True, 0),
        (256, -1),
        (256, KMaxWireId + 1),
        (256, False),
    ),
)
def TestBadHeader(TypeCode: int, ObjectId: int) -> None:
    with Raises(ValueError):
        _ = EmitBulkHeader(TypeCode, ObjectId)


# invalid ownership can never generate metadata offsets for a broken stream
@TestMarks.parametrize(
    ("Records", "ErrorText"),
    (
        ((), "requires at least one primary"),
        ((BulkRecord(256, 0, False, b""),), "requires at least one primary"),
        (
            (BulkRecord(257, 0, True, b""), BulkRecord(256, 1, False, b"")),
            "no primary owner",
        ),
        (
            (BulkRecord(256, 0, True, b""), BulkRecord(257, 0, True, b"")),
            "Duplicate primary",
        ),
        (
            (BulkRecord(256, 0, True, b""), BulkRecord(256, 0, False, b"")),
            "repeats its primary class",
        ),
        ((BulkRecord(256, KMaxWireId, True, b""),), "no next object identity"),
        (
            (BulkRecord(256, 0, CastValue(bool, 1), b""),),
            "Invalid Fusion BulkStream record",
        ),
        (
            (BulkRecord(256, 0, True, CastValue(bytes, bytearray())),),
            "Invalid Fusion BulkStream record",
        ),
    ),
)
def TestBulkBadRows(Records: tuple[BulkRecord, ...], ErrorText: str) -> None:
    with Raises(ValueError, match=ErrorText):
        _ = EmitBulkStream(Records)


# native frame length contributes to the bound even for a very small payload
def TestBulkLimit() -> None:
    Records = (BulkRecord(256, 0, True, b"x"),)
    Payload, _ = EmitBulkStream(Records, MaxBytes=16)
    assert len(Payload) == 16
    with Raises(ValueError, match="size exceeds limit"):
        _ = EmitBulkStream(Records, MaxBytes=15)
    for LimitValue in (0, KMaxBulkBytes + 1, True):
        with Raises(ValueError, match="Invalid Fusion BulkStream size limit"):
            _ = EmitBulkStream(Records, MaxBytes=LimitValue)


# primary and continuation limits protect the two independently counted metadata tables
def TestIndexLimits(MonkeyPatch: PatchContext) -> None:
    MonkeyPatch.setattr(
        "convert.formats.Fusion.SegmentCodec.Bulk.BulkOwners.KMaxIndexRows", 1
    )
    First = BulkRecord(257, 0, True, b"")
    Extra = BulkRecord(257, 1, True, b"")
    Child = BulkRecord(256, 0, False, b"")
    assert len(EmitBulkStream((First, Child))[1]) == 2
    with Raises(ValueError, match="primary count exceeds index limit"):
        _ = EmitBulkStream((First, Extra))
    with Raises(ValueError, match="continuation count exceeds index limit"):
        _ = EmitBulkStream((First, Child, Child))


# real records verify the new framing without relying on a guessed payload model
@TestMarks.parametrize("FileName", ("offset.f3d", "angle.f3d"))
@TestMarks.parametrize("Segment", KCoreSegments)
def TestBulkNative(FileName: str, Segment: SegmentKind) -> None:
    SourcePath = FilePath(__file__).resolve().parents[4] / KFixtureRoot / FileName
    Prefix = f"FusionAssetName[Active]/{Segment.value}1/"
    with ZipFile(SourcePath) as Archive:
        try:
            BulkData = Archive.read(Prefix + "BulkStream.dat")
            MetaData = Archive.read(Prefix + "MetaStream.dat")
        except NotImplementedError:
            SkipCase("The selected Python ZIP reader does not support this compression")
    Spans = ReadBulkSpans(BulkData, MetaData, Segment=Segment)
    Output, Entries = EmitBulkStream(
        BulkRecord(
            SpanValue.TypeCode,
            SpanValue.ObjectId,
            SpanValue.IsPrimary,
            BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset],
        )
        for SpanValue in Spans
    )
    assert Output == BulkData
    assert Entries == tuple(
        (SpanValue.StartOffset, SpanValue.ObjectId, SpanValue.IsPrimary)
        for SpanValue in Spans
    )
    assert ReadBulkSpans(Output, MetaData, Segment=Segment) == Spans
