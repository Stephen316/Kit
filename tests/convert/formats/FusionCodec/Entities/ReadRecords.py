from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord


def ReadRecords(BulkData: bytes, MetaData: bytes) -> tuple[BulkRecord, ...]:
    return tuple(
        BulkRecord(
            SpanValue.TypeCode,
            SpanValue.ObjectId,
            SpanValue.IsPrimary,
            BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset],
        )
        for SpanValue in ReadBulkSpans(BulkData, MetaData)
    )
