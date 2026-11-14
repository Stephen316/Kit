from convert.formats.Fusion.SegmentCodec.Chronology.PackHistRefs import (
    PackHistRef,
    PackHistRefs,
)
from convert.formats.Fusion.SegmentCodec.Parameters.CheckParamScope import (
    CheckParamScope,
)
from convert.formats.Fusion.SegmentCodec.Parameters.ParamScope import ParamScope
from convert.formats.Fusion.SegmentCodec.Parameters.ParamSink import ParamSink


def EmitParamOrder(Value: ParamScope) -> bytes:
    CheckParamScope(Value)
    Output = ParamSink()
    Output.AddBytes(bytes(15))
    Output.AddWord(Value.HighWaterMark)
    Output.AddBytes(PackHistRef(Value.RegistryId))
    Output.AddBytes(bytes(1))
    Output.AddBytes(PackHistRefs(Value.MemberIds))
    Output.AddBytes(PackHistRef(Value.ComponentId))
    return bytes(Output.Buffer)
