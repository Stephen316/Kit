from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef


def ReadVertexPoint(Table: LiveTable, VertexRef: int) -> KJournalVector:
    Vertex = RequireLive(Table, VertexRef, VertexNode)
    OwnerEdge = RequireLive(Table, Vertex.OwnerEdge, EdgeNode)
    if Vertex.EdgeIndex not in (0, 1):
        raise ValueError("Unsupported Fusion linear vertex owner index")
    Expected = OwnerEdge.StartVertex if Vertex.EdgeIndex == 0 else OwnerEdge.EndVertex
    if StableRef(Table, Expected) != VertexRef:
        raise ValueError("Fusion vertex owner does not select this endpoint")
    return RequireLive(Table, Vertex.PointRef, PointNode).PositionCm
