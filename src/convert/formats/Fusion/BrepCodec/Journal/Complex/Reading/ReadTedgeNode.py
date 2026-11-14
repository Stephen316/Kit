from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TedgeNode import TedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Geometry.ReadEdgeNode import (
    ReadEdgeNode,
)


def ReadTedgeNode(Cursor: FieldCursor) -> TedgeNode:
    BaseNode = ReadEdgeNode(Cursor)
    Tolerance = ReadDoubleMut(Cursor)
    SaveVersion = ReadLongMut(Cursor)
    Stamp = ReadLongMut(Cursor)
    return TedgeNode(BaseNode, Tolerance, SaveVersion, Stamp)
