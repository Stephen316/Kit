from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.CheckPolySpec import (
    CheckPolySpec,
)
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.Polyhedron import Polyhedron
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.PolyLayout import PolyLayout


def MakePolyLayout(Model: Polyhedron) -> PolyLayout:
    CheckPolySpec(Model)
    Points = tuple(
        (Point[0] / 10.0, Point[1] / 10.0, Point[2] / 10.0) for Point in Model.PointsMm
    )
    Edges = tuple(
        sorted(
            {
                (
                    min(Start, RingValue[(Index + 1) % len(RingValue)]),
                    max(Start, RingValue[(Index + 1) % len(RingValue)]),
                )
                for RingValue in Model.FaceLoops
                for Index, Start in enumerate(RingValue)
            }
        )
    )
    Starts = tuple(
        sum(len(Value) for Value in Model.FaceLoops[:Index])
        for Index in range(len(Model.FaceLoops))
    )
    Faces = len(Model.FaceLoops)
    Coedges = sum(map(len, Model.FaceLoops))
    EdgeBase = 4 + 2 * Faces + Coedges
    VertexBase = EdgeBase + len(Edges)
    PointBase = VertexBase + len(Points)
    PlaneBase = PointBase + len(Points)
    CurveBase = PlaneBase + Faces
    if CurveBase + len(Edges) > 1024:
        raise ValueError("Fusion polyhedron exceeds the journal entity quota")
    return PolyLayout(
        Points,
        Model.FaceLoops,
        Edges,
        Starts,
        4,
        4 + Faces,
        4 + 2 * Faces,
        EdgeBase,
        VertexBase,
        PointBase,
        PlaneBase,
        CurveBase,
    )
