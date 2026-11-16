from convert.Formats.Fusion.BrepCodec.Journal.Complex.Nodes.TvertexNode import (
    TvertexNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadVertexNode import (
    ReadVertexNode,
)


# the tvertex node operation needs a distinct decoding boundary so nested spline and surface records retain their relationships
def ReadTvertexNode(Cursor: FieldCursor) -> TvertexNode:
    BaseNode = ReadVertexNode(Cursor)
    Sentinel = ReadDoubleMut(Cursor)
    Tolerance = ReadDoubleMut(Cursor)
    SavedTolerance = ReadDoubleMut(Cursor)
    Stamp = ReadLongMut(Cursor)
    return TvertexNode(BaseNode, Sentinel, Tolerance, SavedTolerance, Stamp)
