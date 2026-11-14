from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.formats.Fusion.TSplineCodec.Model.CageFace import CageFace
from convert.formats.Fusion.TSplineCodec.Model.CageEdge import CageEdge
from convert.formats.Fusion.TSplineCodec.Model.CageVertex import CageVertex
from convert.formats.Fusion.TSplineCodec.Model.CageLink import CageLink
from convert.formats.Fusion.TSplineCodec.Model.CageOrientation import (
    CageOrientation,
)
from convert.formats.Fusion.TSplineCodec.Authoring.PickEdgeRoots import (
    PickEdgeRoots,
)
from convert.formats.Fusion.TSplineCodec.Authoring.PickVertRoots import (
    PickVertRoots,
)


def MakeTopology(
    Links: tuple[CageLink, ...],
    VertexCount: int,
    Orientation: CageOrientation | None = None,
) -> CageTopology:
    FaceRoots: dict[int, int] = {}
    for Index, LinkValue in enumerate(Links):
        _ = FaceRoots.setdefault(LinkValue.FaceIndex, Index)
    EdgeRoots = PickEdgeRoots(Links, Orientation)
    VertexRoots = PickVertRoots(Links, VertexCount, Orientation)
    Faces = tuple(CageFace(FaceRoots[Index]) for Index in range(len(FaceRoots)))
    Edges = tuple(CageEdge(EdgeRoots[Index]) for Index in range(len(EdgeRoots)))
    Vertices = tuple(
        CageVertex(VertexRoots[Index], "NORTH") for Index in range(VertexCount)
    )
    return CageTopology(Faces, Edges, Vertices, Links)
