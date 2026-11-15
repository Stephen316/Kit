from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)


# the present decision must stay consistent so revision ownership survives native history reconstruction
def IsPresentMut(Cursor: FieldCursor) -> bool:
    Value = ReadLongMut(Cursor)
    if Value not in (0, 1):
        raise ValueError("Invalid Fusion journal presence marker")
    return Value == 1
