from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Features.EmitFeature import EmitFeature
from convert.formats.Fusion.SegmentCodec.Features.ReadFeature import ReadFeature
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass
from tests.convert.formats.FusionCodec.Parameters.ReadLineage import ReadLineage

KFeatureGuids = frozenset(
    (
        "8DA771B7-52ED-42FC-94E2-2353FE141373",
        "DD405BC2-D673-44F0-8833-5CB2A1C186C7",
    )
)


def RecodeFeatures(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], Classes: tuple[MetaClass, ...]
) -> list[BulkRecord]:
    Owners = {
        Value.ObjectId
        for Value in Spans
        if Value.IsPrimary and Value.ClassGuid in KFeatureGuids
    }
    assert Owners
    Records: list[BulkRecord] = []
    for SpanValue in Spans:
        Payload = BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset]
        if SpanValue.ObjectId in Owners:
            Lineage = ReadLineage(Classes, SpanValue.ClassGuid)
            Rebuilt = EmitFeature(ReadFeature(Payload, Lineage))
            assert Rebuilt == Payload
            Payload = Rebuilt
        Records.append(
            BulkRecord(
                SpanValue.TypeCode, SpanValue.ObjectId, SpanValue.IsPrimary, Payload
            )
        )
    return Records
