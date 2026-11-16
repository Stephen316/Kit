from convert.Formats.Fusion.BulkSpans import ReadBulkSpans
from convert.Formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.DocumentCodec.Records.SlackLimit import (
    KMaxDesignSlack,
    KSlackKinds,
)
from convert.Formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.Formats.Fusion.EntityCodec.DecodeSlack import DecodeSlack
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.MetaIndex import SegmentKind
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


# the doc segment operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadDocSegment(
    Streams: SegmentStreams, Metadata: MetaSegment, Profile: EntityProfile
) -> ParsedSegment:
    if Streams.SegmentId != Metadata.Header.SegmentId:
        raise ValueError("Fusion segment identity disagrees with its metadata")
    Records = tuple(
        BulkRecord(
            SpanValue.TypeCode,
            SpanValue.ObjectId,
            SpanValue.IsPrimary,
            Streams.BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset],
        )
        for SpanValue in ReadBulkSpans(
            Streams.BulkData, Streams.Metadata, Segment=Metadata.Header.Segment
        )
    )
    KindValue = Metadata.Header.Segment
    if KindValue not in KSlackKinds:
        Values = DecodeEntities(Records, Metadata.Classes, Profile)
        return ParsedSegment(Metadata, Values, Profile)
    Values, Slack = DecodeSlack(Records, Metadata.Classes, Profile)
    if KindValue is SegmentKind.KDesign and len(Slack) > KMaxDesignSlack:
        raise ValueError("Unexplained trailing Fusion entity payload bytes")
    return ParsedSegment(Metadata, Values, Profile, Slack)
