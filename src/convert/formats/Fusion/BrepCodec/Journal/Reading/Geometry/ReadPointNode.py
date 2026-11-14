from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadVectorMut import (
    ReadVectorMut,
)


def ReadPointNode(Cursor: FieldCursor) -> PointNode:
    Prefix = ReadPrefixMut(Cursor)
    PositionCm = ReadVectorMut(Cursor, 19)
    return PointNode(Prefix, PositionCm)
