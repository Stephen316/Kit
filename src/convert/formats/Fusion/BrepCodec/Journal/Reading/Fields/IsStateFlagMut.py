from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)


def IsStateFlagMut(Cursor: FieldCursor) -> bool:
    Value = ReadLongMut(Cursor)
    if Value not in (0, 1):
        raise ValueError("Invalid Fusion delta-state boolean")
    return Value == 1
