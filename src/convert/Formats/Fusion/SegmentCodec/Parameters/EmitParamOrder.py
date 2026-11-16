from convert.Formats.Fusion.SegmentCodec.Chronology.PackHistRefs import (
    PackHistRef,
    PackHistRefs,
)
from convert.Formats.Fusion.SegmentCodec.Parameters.CheckParamScope import (
    CheckParamScope,
)
from convert.Formats.Fusion.SegmentCodec.Parameters.ParamScope import ParamScope
from convert.Formats.Fusion.SegmentCodec.Parameters.ParamSink import ParamSink


# the parameter order operation needs a consistent construction rule so native records retain their segment ownership and schema
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
