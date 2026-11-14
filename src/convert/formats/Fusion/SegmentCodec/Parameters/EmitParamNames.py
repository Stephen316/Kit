from convert.formats.Fusion.SegmentCodec.Chronology.PackHistRefs import PackHistRef
from convert.formats.Fusion.SegmentCodec.Parameters.CheckParamScope import (
    CheckParamScope,
)
from convert.formats.Fusion.SegmentCodec.Parameters.ParamScope import ParamScope
from convert.formats.Fusion.SegmentCodec.Parameters.ParamSink import ParamSink


def EmitParamNames(Value: ParamScope) -> bytes:
    CheckParamScope(Value)
    Output = ParamSink()
    Output.AddBytes(bytes(4) + b"\1")
    Output.AddWord(len(Value.MemberIds) + 1)
    for Identity in (Value.CollectionId,) + Value.MemberIds:
        Output.AddBytes(PackHistRef(Identity) + bytes(4))
    Output.AddBytes(bytes(1))
    Output.AddWord(len(Value.NameRows))
    for Identity, Content in Value.NameRows:
        Output.AddParamText(Content)
        Output.AddBytes(PackHistRef(Identity))
    return bytes(Output.Buffer)
