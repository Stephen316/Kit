from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.PolyLayout import PolyLayout


def MakePolyPoints(Layout: PolyLayout) -> tuple[PointNode, ...]:
    return tuple(PointNode(EntityPrefix(-1, -1), Point) for Point in Layout.PointsCm)


def MakePolyVerts(Layout: PolyLayout) -> tuple[VertexNode, ...]:
    Results: list[VertexNode] = []
    for Index in range(len(Layout.PointsCm)):
        EdgeIndex = next(
            Ordinal
            for Ordinal, PairValue in enumerate(Layout.Edges)
            if Index in PairValue
        )
        Endpoint = Layout.Edges[EdgeIndex].index(Index)
        Results.append(
            VertexNode(
                EntityPrefix(-1, -1),
                Layout.EdgeBase + EdgeIndex,
                Endpoint,
                Layout.PointBase + Index,
            )
        )
    return tuple(Results)
