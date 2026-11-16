from convert.Formats.Fusion.BulkSpans import ReadBulkSpans
from convert.Formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.Formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.MetaIndex import SegmentKind
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.Formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire


# shared read auxiliary setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadAuxiliary(
    Streams: SegmentStreams, Profile: EntityProfile, Segment: SegmentKind
) -> tuple[EntityRecord, ...]:
    Metadata = ReadMetaWire(Streams.Metadata, Segment=Segment)
    Spans = ReadBulkSpans(Streams.BulkData, Streams.Metadata, Segment=Segment)
    Records = tuple(
        BulkRecord(
            SpanValue.TypeCode,
            SpanValue.ObjectId,
            SpanValue.IsPrimary,
            Streams.BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset],
        )
        for SpanValue in Spans
    )
    return DecodeEntities(Records, Metadata.Classes, Profile)
