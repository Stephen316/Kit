from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.Formats.Fusion.SegmentCodec.Features.EmitFeature import EmitFeature
from convert.Formats.Fusion.SegmentCodec.Features.ReadFeature import ReadFeature
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass
from tests.Convert.Formats.FusionCodec.Parameters.ReadLineage import ReadLineage

# the feature guids cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KFeatureGuids = frozenset(
    (
        "8DA771B7-52ED-42FC-94E2-2353FE141373",
        "DD405BC2-D673-44F0-8833-5CB2A1C186C7",
    )
)


# shared recode features setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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
