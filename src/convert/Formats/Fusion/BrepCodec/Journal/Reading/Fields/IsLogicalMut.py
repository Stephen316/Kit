from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)


# the logical decision must stay consistent so revision ownership survives native history reconstruction
def IsLogicalMut(Cursor: FieldCursor) -> bool:
    TagValue, Value = ReadFieldMut(Cursor)
    if TagValue not in (10, 11) or Value is not None:
        raise ValueError("Invalid Fusion journal logical value")
    return TagValue == 10
