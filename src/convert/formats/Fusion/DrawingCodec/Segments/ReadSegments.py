from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSegment import ReadDocSegment
from convert.formats.Fusion.DrawingCodec.Legacy.LegacySegment import LegacySegment
from convert.formats.Fusion.DrawingCodec.Legacy.ReadLegacy import ReadLegacy
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingAsset import DrawingAsset
from convert.formats.Fusion.DrawingCodec.Manifest.ManifestRules import KModernVersion
from convert.formats.Fusion.DrawingCodec.Segments.DrawingProfile import DrawingProfile
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

KDrawingKinds = frozenset((SegmentKind.KDrawingDesign, SegmentKind.KDrawingAct))


def ReadSegmentsMut(
    Asset: DrawingAsset, Folders: tuple[str, ...], Members: dict[str, bytes]
) -> tuple[ParsedSegment | LegacySegment, ...]:
    Pairs: list[tuple[bytes, bytes]] = []
    for Folder in Folders:
        MetaData = Members.pop(Folder + "MetaStream.dat", None)
        BulkData = Members.pop(Folder + "BulkStream.dat", None)
        if MetaData is None or BulkData is None:
            raise ValueError("Missing Fusion drawing segment stream")
        Pairs.append((MetaData, BulkData))
    if Asset.Version != KModernVersion:
        Legacy = tuple(ReadLegacy(MetaData, BulkData) for MetaData, BulkData in Pairs)
        for SlotValue, Segment in zip(Asset.Segments, Legacy, strict=True):
            if (SlotValue.SegmentId, SlotValue.SegmentType) != (
                Segment.Header.SegmentId,
                Segment.Header.Kind,
            ):
                raise ValueError(
                    "Legacy Fusion drawing segment disagrees with its slot"
                )
        return Legacy
    Metadata: list[MetaSegment] = []
    for SlotValue, (MetaData, _) in zip(Asset.Segments, Pairs, strict=True):
        if SlotValue.SegmentType not in KDrawingKinds:
            raise ValueError("Unsupported Fusion drawing segment type")
        Value = ReadMetaWire(MetaData, Segment=SegmentKind(SlotValue.SegmentType))
        if Value.Header.SegmentId != SlotValue.SegmentId:
            raise ValueError("Fusion drawing segment disagrees with its slot")
        Metadata.append(Value)
    Known = tuple(Metadata)
    return tuple(
        ReadDocSegment(
            SegmentStreams(Value.Header.SegmentId, MetaData, BulkData),
            Value,
            DrawingProfile(Known, Value.Header.SegmentId),
        )
        for Value, (MetaData, BulkData) in zip(Known, Pairs, strict=True)
    )
