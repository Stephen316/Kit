from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


def ReadPrefixMut(Cursor: FieldCursor) -> EntityPrefix:
    Prefix = EntityPrefix(ReadRefMut(Cursor), ReadLongMut(Cursor))
    NeedFieldMut(Cursor, (12, -1))
    return Prefix
