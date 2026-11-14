from dataclasses import replace as Replace
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMark, raises as Raises

from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Records.EmitDocSegment import (
    EmitDocSegment,
)
from convert.formats.Fusion.MetaIndex import SegmentKind

KSavedRoot = (
    FilePath(__file__).resolve().parents[5]
    / "re"
    / "Fusion"
    / "LocalOracle"
    / "LinksConfigs"
    / "Fixtures"
    / "KitAsmRootSaved.f3d"
)

KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)


def SegmentOfKind(
    Segments: tuple[ParsedSegment, ...], KindValue: SegmentKind
) -> ParsedSegment:
    Matches = [
        Segment for Segment in Segments if Segment.Metadata.Header.Segment is KindValue
    ]
    assert len(Matches) == 1
    return Matches[0]


@KRequiresCodec
def TestSavedRoot() -> None:
    Payload = KSavedRoot.read_bytes()
    Model = ReadDocument(Payload)
    Design = SegmentOfKind(Model.Segments, SegmentKind.KDesign)
    assert len(Design.BulkSlack) == 10
    assert sum(len(Segment.BulkSlack) for Segment in Model.Segments) == 10
    assert len(Model.Document.Links) == 2
    assert [len(Segment.Metadata.Contexts) for Segment in Model.Segments] == [2, 2, 2]
    Original = {Stream.SegmentId: Stream for Stream in ReadContainer(Payload).Streams}
    for Segment in Model.Segments:
        Emitted = EmitDocSegment(Segment)
        assert Emitted == Original[Segment.Metadata.Header.SegmentId]
    assert Original[Design.Metadata.Header.SegmentId].BulkData.endswith(
        Design.BulkSlack
    )
    assert ReadDocument(EmitParsed(Model)) == Model


@KRequiresCodec
def TestSlackBound() -> None:
    Container = ReadContainer(KSavedRoot.read_bytes())
    Design = SegmentOfKind(
        ReadDocument(KSavedRoot.read_bytes()).Segments, SegmentKind.KDesign
    )
    Identity = Design.Metadata.Header.SegmentId
    Streams = tuple(
        (
            Replace(Stream, BulkData=Stream.BulkData + bytes(7))
            if Stream.SegmentId == Identity
            else Stream
        )
        for Stream in Container.Streams
    )
    with Raises(ValueError, match="trailing Fusion entity payload"):
        _ = ReadDocument(EmitContainer(Replace(Container, Streams=Streams)))
    with Raises(ValueError, match="exceeds its limit"):
        _ = EmitDocSegment(Replace(Design, BulkSlack=Design.BulkSlack + bytes(7)))
