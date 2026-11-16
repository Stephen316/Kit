from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.PolyAuthor.Polyhedron import Polyhedron
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp

# the planar history cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KPlanarHistory = HistoryState(4, 2, 4, 1, 2)

# the planar stamp cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KPlanarStamp = GeometryStamp("Kit", "Planar integration", "2026-11-12T00:00:00Z")

# the planar place cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KPlanarPlace = TransformNode(
    -1,
    -1,
    (0.0, 1.0, 0.0),
    (-1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0),
    (1.1, -0.7, 0.5),
    1.25,
    True,
    False,
    False,
)


# shared make tetrahedron setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def MakeTetrahedron() -> Polyhedron:
    return Polyhedron(
        ((0.0, 0.0, 0.0), (17.0, 0.0, 0.0), (0.0, 23.0, 0.0), (0.0, 0.0, 31.0)),
        ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)),
    )


# shared make tri prism setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def MakeTriPrism() -> Polyhedron:
    return Polyhedron(
        (
            (0.0, 0.0, 0.0),
            (19.0, 0.0, 0.0),
            (0.0, 13.0, 0.0),
            (0.0, 0.0, 37.0),
            (19.0, 0.0, 37.0),
            (0.0, 13.0, 37.0),
        ),
        ((0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)),
    )
