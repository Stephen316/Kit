from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


def ReadBodyNode(Cursor: FieldCursor) -> BodyNode:
    Prefix = ReadPrefixMut(Cursor)
    FirstLump = ReadRefMut(Cursor)
    NeedFieldMut(Cursor, (12, -1))
    TransformRef = ReadRefMut(Cursor)
    return BodyNode(Prefix, FirstLump, TransformRef)
