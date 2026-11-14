from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment
from convert.formats.Fusion.DrawingCodec.Legacy.EmitLegacy import EmitLegacy
from convert.formats.Fusion.DrawingCodec.Legacy.LegacySegment import LegacySegment
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingAsset import DrawingAsset
from convert.formats.Fusion.DrawingCodec.Manifest.ManifestRules import KModernVersion


def EmitSegments(
    Asset: DrawingAsset,
    Folders: tuple[str, ...],
    Segments: tuple[ParsedSegment | LegacySegment, ...],
) -> dict[str, bytes]:
    if len(Segments) != len(Asset.Segments):
        raise ValueError("Fusion drawing segments disagree with the asset manifest")
    Result: dict[str, bytes] = {}
    IsModern = Asset.Version == KModernVersion
    for SlotValue, Folder, Segment in zip(
        Asset.Segments, Folders, Segments, strict=True
    ):
        if isinstance(Segment, ParsedSegment) and IsModern:
            Header = Segment.Metadata.Header
            if (Header.SegmentId, Header.Segment.value) != (
                SlotValue.SegmentId,
                SlotValue.SegmentType,
            ):
                raise ValueError("Fusion drawing segment disagrees with its slot")
            Streams = EmitDocSegment(Segment)
            MetaStream, BulkStream = Streams.Metadata, Streams.BulkData
        elif isinstance(Segment, LegacySegment) and not IsModern:
            if (Segment.Header.SegmentId, Segment.Header.Kind) != (
                SlotValue.SegmentId,
                SlotValue.SegmentType,
            ):
                raise ValueError(
                    "Legacy Fusion drawing segment disagrees with its slot"
                )
            BulkStream, MetaStream = EmitLegacy(Segment)
        else:
            raise ValueError(
                "Fusion drawing segment generation disagrees with manifest"
            )
        Result[Folder + "MetaStream.dat"] = MetaStream
        Result[Folder + "BulkStream.dat"] = BulkStream
    return Result
