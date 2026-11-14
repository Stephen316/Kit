from math import dist as Distance

from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.formats.Fusion.BrepCodec.Journal.Planar.VectorMath import (
    Normalize,
    Subtract,
)
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.PolyLayout import PolyLayout


def MakePolyEdges(
    Layout: PolyLayout, Coedges: tuple[CoedgeNode, ...]
) -> tuple[EdgeNode, ...]:
    Results: list[EdgeNode] = []
    for Index, (Start, Finish) in enumerate(Layout.Edges):
        OwnerIndex = next(
            Ordinal
            for Ordinal, Value in enumerate(Coedges)
            if Value.EdgeRef == Layout.EdgeBase + Index
        )
        Length = Distance(Layout.PointsCm[Start], Layout.PointsCm[Finish])
        Results.append(
            EdgeNode(
                EntityPrefix(-1, -1),
                Layout.VertexBase + Start,
                0.0,
                Layout.VertexBase + Finish,
                Length,
                Layout.CoedgeBase + OwnerIndex,
                Layout.CurveBase + Index,
                False,
                "unknown",
            )
        )
    return tuple(Results)


def MakePolyCurves(Layout: PolyLayout) -> tuple[StraightNode, ...]:
    Results: list[StraightNode] = []
    for Start, Finish in Layout.Edges:
        First = Layout.PointsCm[Start]
        Second = Layout.PointsCm[Finish]
        Results.append(
            StraightNode(
                EntityPrefix(-1, -1),
                First,
                Normalize(Subtract(Second, First)),
                0.0,
                Distance(First, Second),
            )
        )
    return tuple(Results)
