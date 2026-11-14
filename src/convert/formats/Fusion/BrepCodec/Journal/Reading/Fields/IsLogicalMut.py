from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)


def IsLogicalMut(Cursor: FieldCursor) -> bool:
    TagValue, Value = ReadFieldMut(Cursor)
    if TagValue not in (10, 11) or Value is not None:
        raise ValueError("Invalid Fusion journal logical value")
    return TagValue == 10
