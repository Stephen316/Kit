from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TvertexNode import (
    TvertexNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadVertexNode import (
    ReadVertexNode,
)


def ReadTvertexNode(Cursor: FieldCursor) -> TvertexNode:
    BaseNode = ReadVertexNode(Cursor)
    Sentinel = ReadDoubleMut(Cursor)
    Tolerance = ReadDoubleMut(Cursor)
    SavedTolerance = ReadDoubleMut(Cursor)
    Stamp = ReadLongMut(Cursor)
    return TvertexNode(BaseNode, Sentinel, Tolerance, SavedTolerance, Stamp)
