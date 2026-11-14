from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


def ReadVertexNode(Cursor: FieldCursor) -> VertexNode:
    Prefix = ReadPrefixMut(Cursor)
    OwnerEdge = ReadRefMut(Cursor)
    EdgeIndex = ReadLongMut(Cursor)
    PointRef = ReadRefMut(Cursor)
    return VertexNode(Prefix, OwnerEdge, EdgeIndex, PointRef)
