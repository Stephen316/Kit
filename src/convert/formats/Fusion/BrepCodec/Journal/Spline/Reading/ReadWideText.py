from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.WideWord import WideWord


def ReadWideText(Cursor: FieldCursor) -> str:
    TagValue, Value = ReadFieldMut(Cursor)
    if TagValue not in (7, 8, 9) or type(Value) is not str or not Value.isascii():
        raise ValueError("Invalid Fusion journal program text")
    if WideWord(Value)[0] != TagValue:
        raise ValueError("Noncanonical Fusion journal text width")
    return Value
