from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)


# the state flag decision must stay consistent so revision ownership survives native history reconstruction
def IsStateFlagMut(Cursor: FieldCursor) -> bool:
    Value = ReadLongMut(Cursor)
    if Value not in (0, 1):
        raise ValueError("Invalid Fusion delta-state boolean")
    return Value == 1
