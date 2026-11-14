from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)


def ReadNameMut(Cursor: FieldCursor) -> str:
    TagValue, Value = ReadFieldMut(Cursor)
    if TagValue != 13 or type(Value) is not str or not Value or not Value.isascii():
        raise ValueError("Invalid Fusion journal subtype name")
    return Value
