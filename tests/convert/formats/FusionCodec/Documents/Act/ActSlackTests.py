from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Records.EmitDocSegment import (
    EmitDocSegment,
)
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from tests.convert.formats.FusionCodec.Documents.Act.SlackSources import KSlackCases
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)


def PickSegment(
    Segments: tuple[ParsedSegment, ...], KindValue: SegmentKind
) -> ParsedSegment:
    Matches = [
        Segment for Segment in Segments if Segment.Metadata.Header.Segment is KindValue
    ]
    assert len(Matches) == 1
    return Matches[0]


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion archive requires ZIP Zstandard"
)
@MarkTests.parametrize(
    "CaseValue", KSlackCases, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestActSlack(CaseValue: tuple[str, str, int]) -> None:
    Payload = ReadFormFile(CaseValue[0], CaseValue[1])
    Model = ReadDocument(Payload)
    ActSegment = PickSegment(Model.Segments, SegmentKind.KAct)
    assert len(ActSegment.BulkSlack) == CaseValue[2]
    assert sum(len(Segment.BulkSlack) for Segment in Model.Segments) == CaseValue[2]
    Original = {Stream.SegmentId: Stream for Stream in ReadContainer(Payload).Streams}
    for Segment in Model.Segments:
        Emitted = EmitDocSegment(Segment)
        assert Emitted == Original[Segment.Metadata.Header.SegmentId]
    assert ReadDocument(EmitParsed(Model)) == Model


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion archive requires ZIP Zstandard"
)
def TestSlackDrop() -> None:
    Model = ReadDocument(ReadFormFile(*KSlackCases[1][:2]))
    Segments = tuple(ReplaceValue(Segment, BulkSlack=b"") for Segment in Model.Segments)
    Clean = ReplaceValue(Model, Segments=Segments)
    Reopened = ReadDocument(EmitParsed(Clean))
    assert Reopened == Clean
    assert PickSegment(Reopened.Segments, SegmentKind.KAct).Records == (
        PickSegment(Model.Segments, SegmentKind.KAct).Records
    )


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion archive requires ZIP Zstandard"
)
def TestSlackGate() -> None:
    Model = ReadDocument(ReadFormFile(*KSlackCases[0][:2]))
    Design = PickSegment(Model.Segments, SegmentKind.KDesign)
    Padded = EmitDocSegment(ReplaceValue(Design, BulkSlack=b"\0\0"))
    assert Padded.BulkData == EmitDocSegment(Design).BulkData + b"\0\0"
    with RaisesError(ValueError, match="exceeds its limit"):
        _ = EmitDocSegment(ReplaceValue(Design, BulkSlack=bytes(17)))
    Browser = PickSegment(Model.Segments, SegmentKind.KBrowser)
    Trailed = EmitDocSegment(ReplaceValue(Browser, BulkSlack=b"\0\0"))
    assert Trailed.BulkData == EmitDocSegment(Browser).BulkData + b"\0\0"
    ActSegment = PickSegment(Model.Segments, SegmentKind.KAct)
    Mutable = CastValue(bytes, bytearray(2))
    with RaisesError(ValueError, match="must be bytes"):
        _ = EmitDocSegment(ReplaceValue(ActSegment, BulkSlack=Mutable))


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion archive requires ZIP Zstandard"
)
def TestOtherTrail() -> None:
    Archive = TrailArchive(SegmentKind.KDesign, 17)
    with RaisesError(ValueError, match="trailing Fusion entity payload"):
        _ = ReadDocument(Archive)


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion archive requires ZIP Zstandard"
)
def TestBrowserTail() -> None:
    Model = ReadDocument(TrailArchive(SegmentKind.KBrowser, 2))
    Browser = PickSegment(Model.Segments, SegmentKind.KBrowser)
    assert Browser.BulkSlack == bytes(2)
    assert ReadDocument(EmitParsed(Model)) == Model


def TrailArchive(KindValue: SegmentKind, Length: int) -> bytes:
    Container = ReadContainer(ReadFormFile(*KSlackCases[0][:2]))
    Streams = tuple(
        (
            ReplaceValue(Stream, BulkData=Stream.BulkData + bytes(Length))
            if ReadMetaWire(Stream.Metadata).Header.Segment is KindValue
            else Stream
        )
        for Stream in Container.Streams
    )
    return EmitContainer(ReplaceValue(Container, Streams=Streams))
