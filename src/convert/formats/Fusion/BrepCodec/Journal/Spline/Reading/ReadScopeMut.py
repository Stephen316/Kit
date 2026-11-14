from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef


def ReadScopeMut(Cursor: FieldCursor, Family: str) -> str | SubtypeRef:
    NeedFieldMut(Cursor, (15, None))
    TagValue, Value = ReadFieldMut(Cursor)
    if TagValue != 13 or type(Value) is not str or not Value.isascii():
        raise ValueError("Invalid Fusion journal subtype name")
    if Value != "ref":
        return Value
    Index = ReadLongMut(Cursor)
    NeedFieldMut(Cursor, (16, None))
    if Index < 0:
        raise ValueError("Invalid Fusion journal subtype table reference")
    return SubtypeRef(Family, Index)
