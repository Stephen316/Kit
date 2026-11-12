from typing import cast as CastValue

from convert.formats.Fusion.SegmentCodec.Metadata.CheckWireBody import CheckWireBody
from convert.formats.Fusion.SegmentCodec.Metadata.EmitWireHead import EmitWireHead
from convert.formats.Fusion.SegmentCodec.Metadata.EmitWireRows import (
    EmitWireClasses,
    EmitWireProps,
    EmitWireTable,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaLimits import KMaxMetaIds
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink


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
    EmitWireProps(SinkValue, Value.Properties)
    CheckWireBody(Value)
    return bytes(SinkValue.Buffer)
