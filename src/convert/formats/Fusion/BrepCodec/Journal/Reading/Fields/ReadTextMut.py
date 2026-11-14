from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)


def ReadTextMut(Cursor: FieldCursor) -> str:
    TagValue, Value = ReadFieldMut(Cursor)
    if TagValue != 7 or type(Value) is not str or not Value.isascii():
        raise ValueError("Invalid qualified Fusion journal text")
    return Value
