from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Chronology.PackHistRefs import PackHistRef
from convert.formats.Fusion.SegmentCodec.Parameters.NumberBinding import NumberBinding
from convert.formats.Fusion.SegmentCodec.Parameters.ParamSink import ParamSink


def EmitNumBinding(Value: NumberBinding) -> bytes:
    References = tuple(
        PackHistRef(Identity)
        for Identity in (Value.OwnerId, Value.ParamId, Value.BookId)
    )
    if (
        0 in (Value.OwnerId, Value.ParamId, Value.BookId)
        or len(set(References)) != 3
        or type(Value.RuntimeParamId) is not int
        or not 1 <= Value.RuntimeParamId < 1 << 64
        or type(Value.ObserverIndex) is not int
        or not -1 <= Value.ObserverIndex < 1 << 31
    ):
        raise ValueError("Invalid Fusion numeric binding identities or observer index")
    Owner, Param, BookRef = References
    Output = ParamSink()
    Output.AddBytes(bytes(4) + b"\1\1\0\0\0" + Owner)
    Output.AddBytes(PackValue("<i", Value.ObserverIndex))
    Output.AddBytes(bytes(1))
    Output.AddNumber(Value.Number)
    Output.AddBytes(Param)
    Output.AddLong(Value.RuntimeParamId)
    Output.AddBytes(Owner + b"\1\0\0" + BookRef + bytes(1) + Owner)
    return bytes(Output.Buffer)
