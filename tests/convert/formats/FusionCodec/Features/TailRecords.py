from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord


def TailRecords(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], ClassGuid: str | None
) -> list[BulkRecord]:
    Records: list[BulkRecord] = []
    Changed = 0
    for SpanValue in Spans:
        Payload = BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset]
        if (
            ClassGuid is not None
            and SpanValue.IsPrimary
            and SpanValue.ClassGuid.upper() == ClassGuid.upper()
        ):
            Payload += b"\0"
            Changed += 1
        Records.append(
            BulkRecord(
                SpanValue.TypeCode, SpanValue.ObjectId, SpanValue.IsPrimary, Payload
            )
        )
    assert Changed == (0 if ClassGuid is None else 1)
    return Records
