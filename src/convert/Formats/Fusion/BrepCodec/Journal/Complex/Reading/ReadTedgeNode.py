from convert.Formats.Fusion.BrepCodec.Journal.Complex.Nodes.TedgeNode import TedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadEdgeNode import (
    ReadEdgeNode,
)


# the tedge node operation needs a distinct decoding boundary so nested spline and surface records retain their relationships
def ReadTedgeNode(Cursor: FieldCursor) -> TedgeNode:
    BaseNode = ReadEdgeNode(Cursor)
    Tolerance = ReadDoubleMut(Cursor)
    SaveVersion = ReadLongMut(Cursor)
    Stamp = ReadLongMut(Cursor)
    return TedgeNode(BaseNode, Tolerance, SaveVersion, Stamp)
