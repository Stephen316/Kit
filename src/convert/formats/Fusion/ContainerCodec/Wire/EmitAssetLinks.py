from typing import cast as CastValue

from convert.formats.Fusion.ContainerCodec.Model.AssetLink import AssetLink
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import (
    KAssetMarker,
    KMaxLinks,
    KUnchangedGuid,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink


def EmitAssetLinks(SinkValue: ManifestSink, Links: tuple[AssetLink, ...]) -> None:
    SinkValue.AddCount(Links, KMaxLinks)
    LinkIds: set[str] = set()
    for Entry in Links:
        if not isinstance(CastValue(object, Entry), AssetLink) or (
            Entry.LinkId in LinkIds
        ):
            raise ValueError("Invalid or duplicate Fusion asset link")
        LinkIds.add(Entry.LinkId)
        SinkValue.AddGuid(Entry.LinkId)
        SinkValue.AddGuid(Entry.AssetId)
        SinkValue.AddGuid(Entry.SnapshotId)
        SinkValue.AddWord(Entry.LinkWord)
        SinkValue.AddWord(KAssetMarker)
        if Entry.PhysicalGuid == KUnchangedGuid:
            SinkValue.AddText(Entry.PhysicalGuid, WideText=True)
        else:
            SinkValue.AddGuid(Entry.PhysicalGuid)
