from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue

from pytest import mark as MarkTests, raises as RaisesError

from convert.Formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Records.EmitDocSegment import (
    EmitDocSegment,
)
from convert.Formats.Fusion.MetaIndex import SegmentKind
from convert.Formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from tests.Convert.Formats.FusionCodec.Documents.Act.SlackSources import KSlackCases
from tests.Convert.Formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)


# shared pick segment setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def PickSegment(
    Segments: tuple[ParsedSegment, ...], KindValue: SegmentKind
) -> ParsedSegment:
    Matches = [
        Segment for Segment in Segments if Segment.Metadata.Header.Segment is KindValue
    ]
    assert len(Matches) == 1
    return Matches[0]


# the act slack contract needs boundary coverage so stored document relationships remain consistent
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


# the slack drop contract needs boundary coverage so stored document relationships remain consistent
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


# the slack gate contract needs boundary coverage so stored document relationships remain consistent
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


# the other trail contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion archive requires ZIP Zstandard"
)
def TestOtherTrail() -> None:
    Archive = TrailArchive(SegmentKind.KDesign, 17)
    with RaisesError(ValueError, match="trailing Fusion entity payload"):
        _ = ReadDocument(Archive)


# the browser tail contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion archive requires ZIP Zstandard"
)
def TestBrowserTail() -> None:
    Model = ReadDocument(TrailArchive(SegmentKind.KBrowser, 2))
    Browser = PickSegment(Model.Segments, SegmentKind.KBrowser)
    assert Browser.BulkSlack == bytes(2)
    assert ReadDocument(EmitParsed(Model)) == Model


# shared trail archive setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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
