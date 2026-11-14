from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)


def ReadLongMut(Cursor: FieldCursor, TagValue: int = 4) -> int:
    Actual, Value = ReadFieldMut(Cursor)
    if Actual != TagValue or type(Value) is not int:
        raise ValueError("Invalid Fusion journal integer")
    if TagValue == 4 and not -(1 << 31) <= Value < (1 << 31):
        raise ValueError("Fusion journal native integer exceeds signed 32 bits")
    return Value
