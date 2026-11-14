from re import fullmatch as MatchFull

from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.SegmentCodec.Chronology.PackHistRefs import PackHistRef
from convert.formats.Fusion.SegmentCodec.Parameters.CheckParamMeta import CheckParamMeta
from convert.formats.Fusion.SegmentCodec.Parameters.ParamSink import ParamSink


def EmitNumeric(Value: NativeParam) -> bytes:
    if (
        type(Value.RoleName) is not str
        or not Value.RoleName
        or type(Value.ParamName) is not str
        or MatchFull(r"[A-Za-z_][A-Za-z_0-9]*", Value.ParamName) is None
        or type(Value.NativeIndex) is not int
        or not 1 <= Value.NativeIndex < 1 << 32
        or type(Value.CollectionId) is not int
        or not 1 <= Value.CollectionId < 1 << 64
    ):
        raise ValueError("Invalid Fusion numeric parameter fields")
    if Value.BindingId is None:
        if Value.RoleName != "User Parameter":
            raise ValueError("Unbound Fusion parameter must have the user role")
        Binding = bytes(1)
    else:
        Binding = PackHistRef(Value.BindingId)
        if Value.BindingId == 0 or Value.BindingId == Value.CollectionId:
            raise ValueError("Invalid Fusion numeric binding identity")
    Favorite, Extended = CheckParamMeta(Value)
    Output = ParamSink()
    Output.AddBytes(bytes(11) + b"\x06" + bytes(4))
    Output.AddParamText(Value.Comment, AllowControls=True)
    Output.AddWord(Value.NativeIndex)
    Output.AddBytes(Binding)
    Output.AddParamText(Value.Formula)
    Output.AddWord(0)
    Output.AddBytes(bytes(3))
    if Extended:
        Output.AddBytes(bytes(1))
    Output.AddBytes(bytes((Favorite, 0, Value.BindingId is None)))
    for Content in (Value.RoleName, "", Value.DisplayUnit, Value.ParamName):
        Output.AddParamText(Content)
    Output.AddNumber(Value.Number)
    Output.AddBytes(bytes(1) + PackHistRef(Value.CollectionId))
    return bytes(Output.Buffer)
