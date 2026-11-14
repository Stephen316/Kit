from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)


def ReadCountMut(Cursor: FieldCursor, Maximum: int) -> int:
    Count = ReadLongMut(Cursor)
    if not 0 <= Count <= Maximum:
        raise ValueError("Fusion journal count exceeds its bounds")
    return Count
