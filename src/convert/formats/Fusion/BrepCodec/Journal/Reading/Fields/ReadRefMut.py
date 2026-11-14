from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)


def ReadRefMut(Cursor: FieldCursor) -> int:
    Value = ReadLongMut(Cursor, 12)
    if Value < -1:
        raise ValueError("Invalid Fusion journal reference")
    return Value
