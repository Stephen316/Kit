from typing import cast as CastValue

from convert.Formats.Fusion.SegmentCodec.Metadata.CheckWireBody import CheckWireBody
from convert.Formats.Fusion.SegmentCodec.Metadata.EmitMetaCtx import EmitMetaCtx
from convert.Formats.Fusion.SegmentCodec.Metadata.EmitWireHead import EmitWireHead
from convert.Formats.Fusion.SegmentCodec.Metadata.EmitWireRows import (
    EmitWireClasses,
    EmitWireProps,
    EmitWireTable,
)
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaLimits import KMaxMetaIds
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink


# typed models can originate new metadata bytes without borrowing a saved record
def WriteMetaWire(Value: MetaSegment) -> bytes:
    if not isinstance(CastValue(object, Value), MetaSegment):
        raise ValueError("Expected a typed Fusion MetaStream")
    SinkValue = MetaSink()
    EmitWireHead(SinkValue, Value.Header)
    EmitWireClasses(SinkValue, Value.Classes)
    SinkValue.AddCount(Value.StoredIds, KMaxMetaIds)
    for Identity in Value.StoredIds:
        SinkValue.AddLong(Identity)
    EmitWireTable(SinkValue, Value.Primary)
    EmitWireTable(SinkValue, Value.Continuations)
    SinkValue.AddLong(Value.NextId)
    SinkValue.AddWord(Value.Reserved)
    EmitMetaCtx(SinkValue, Value.Contexts)
    EmitWireProps(SinkValue, Value.Properties)
    CheckWireBody(Value)
    return bytes(SinkValue.Buffer)
