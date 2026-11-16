from convert.Formats.Fusion.BulkSpans import ReadBulkSpans
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord


# shared read records setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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
