from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


# the prefix operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadPrefixMut(Cursor: FieldCursor) -> EntityPrefix:
    Prefix = EntityPrefix(ReadRefMut(Cursor), ReadLongMut(Cursor))
    NeedFieldMut(Cursor, (12, -1))
    return Prefix
