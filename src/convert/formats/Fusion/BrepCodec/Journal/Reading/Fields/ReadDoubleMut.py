from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)


def ReadDoubleMut(Cursor: FieldCursor) -> float:
    TagValue, Value = ReadFieldMut(Cursor)
    if TagValue != 6 or type(Value) is not float:
        raise ValueError("Invalid Fusion journal number")
    return Value
