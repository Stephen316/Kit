from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)


# the double operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadDoubleMut(Cursor: FieldCursor) -> float:
    TagValue, Value = ReadFieldMut(Cursor)
    if TagValue != 6 or type(Value) is not float:
        raise ValueError("Invalid Fusion journal number")
    return Value
