from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.MetaCursor import MetaCursor


def ReadFlagMut(Cursor: MetaCursor) -> bool | int:
    ByteValue = Cursor.TakeBytes(1)[0]
    return bool(ByteValue) if ByteValue < 2 else ByteValue


def EmitFlag(Value: KEntityValue) -> bytes:
    if type(Value) is bool or type(Value) is int and 1 < Value < 256:
        return bytes((int(Value),))
    raise ValueError("Fusion entity flag requires a boolean or a set byte")
