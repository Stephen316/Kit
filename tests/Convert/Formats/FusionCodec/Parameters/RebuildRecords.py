from collections.abc import Callable

from convert.Formats.Fusion.NativeParam import NativeParam
from convert.Formats.Fusion.NumericParam import KParamGuid, ReadNativeNum
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.Formats.Fusion.SegmentCodec.Parameters.EmitNumBinding import EmitNumBinding
from convert.Formats.Fusion.SegmentCodec.Parameters.EmitNumeric import EmitNumeric
from convert.Formats.Fusion.SegmentCodec.Parameters.EmitParamNames import EmitParamNames
from convert.Formats.Fusion.SegmentCodec.Parameters.EmitParamOrder import EmitParamOrder
from convert.Formats.Fusion.SegmentCodec.Parameters.ParamScope import ParamScope
from convert.Formats.Fusion.SegmentCodec.Parameters.ReadNumBinding import ReadNumBinding


# shared rebuild records setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def RebuildRecords(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Scope: ParamScope,
    ChangeValue: Callable[[NativeParam], NativeParam] | None,
) -> list[BulkRecord]:
    Replacements = {
        Scope.CollectionId: EmitParamOrder(Scope),
        Scope.RegistryId: EmitParamNames(Scope),
    }
    Records: list[BulkRecord] = []
    for SpanValue in Spans:
        Payload = BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset]
        Original = Payload
        if SpanValue.IsPrimary and SpanValue.ClassGuid == KParamGuid:
            assert Payload[:4] == bytes(4)
            Value = ReadNativeNum(Payload[4:])
            if ChangeValue is not None:
                Value = ChangeValue(Value)
            Payload = EmitNumeric(Value)
        elif (
            SpanValue.IsPrimary
            and SpanValue.ClassGuid == "D91D429C-1BB5-4640-B49F-69AF14F463E9"
        ):
            Payload = EmitNumBinding(ReadNumBinding(Payload))
        elif SpanValue.IsPrimary and SpanValue.ObjectId in Replacements:
            Payload = Replacements[SpanValue.ObjectId]
        if ChangeValue is None:
            assert Payload == Original
        Records.append(
            BulkRecord(
                SpanValue.TypeCode, SpanValue.ObjectId, SpanValue.IsPrimary, Payload
            )
        )
    return Records
