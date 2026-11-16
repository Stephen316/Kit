from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)


# the bound operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadBoundMut(Cursor: FieldCursor) -> float | None:
    return ReadDoubleMut(Cursor) if IsLogicalMut(Cursor) else None
