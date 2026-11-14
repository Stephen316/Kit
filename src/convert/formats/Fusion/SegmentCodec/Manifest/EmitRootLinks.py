from typing import cast as CastValue

from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import (
    KLinkWords,
    KMaxLinkProps,
    KMaxLinks,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLink import ManifestLink
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink


def EmitLinkProps(
    SinkValue: ManifestSink, Properties: tuple[tuple[str, str], ...]
) -> None:
    SinkValue.AddCount(Properties, KMaxLinkProps)
    Names: set[str] = set()
    for Entry in Properties:
        if (
            type(Entry) is not tuple
            or len(CastValue(tuple[object, ...], Entry)) != 2
            or type(Entry[0]) is not str
            or type(Entry[1]) is not str
            or not Entry[0]
            or Entry[0] in Names
        ):
            raise ValueError("Invalid Fusion root manifest link property")
        Names.add(Entry[0])
        SinkValue.AddText(Entry[0], WideText=True)
        SinkValue.AddText(Entry[1], WideText=True)


def EmitRootLinks(SinkValue: ManifestSink, Links: tuple[ManifestLink, ...]) -> None:
    if type(Links) is not tuple or len(Links) > KMaxLinks:
        raise ValueError("Invalid Fusion root manifest link table")
    if not Links:
        SinkValue.AddBytes(b"\0")
        return
    SinkValue.AddBytes(b"\1")
    SinkValue.AddWord(len(Links))
    LinkIds: set[str] = set()
    for Entry in Links:
        if not isinstance(CastValue(object, Entry), ManifestLink) or (
            Entry.LinkId in LinkIds
        ):
            raise ValueError("Invalid or duplicate Fusion root manifest link")
        LinkIds.add(Entry.LinkId)
        SinkValue.AddGuid(Entry.LinkId)
        for PathText in (Entry.SourcePath, Entry.CachePath, Entry.XrefPath):
            SinkValue.AddText(PathText, WideText=True)
        for Number in KLinkWords:
            SinkValue.AddWord(Number)
        EmitLinkProps(SinkValue, Entry.Properties)
