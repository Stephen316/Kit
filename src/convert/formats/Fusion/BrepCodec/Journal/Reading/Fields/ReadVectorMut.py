from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


def ReadVectorMut(Cursor: FieldCursor, TagValue: int) -> KJournalVector:
    Actual, Value = ReadFieldMut(Cursor)
    if Actual != TagValue or not isinstance(Value, tuple) or len(Value) != 3:
        raise ValueError("Invalid Fusion journal vector")
    return Value[0], Value[1], Value[2]
