from convert.formats.Fusion.Sketches.FaceSupport.FaceRecipes import KEdgeNames
from convert.formats.Fusion.Topology.AsmEdge.AsmFaceRim import ReadIncidence
from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from typing import TypeAlias

# preserve the selected native edge and both endpoints in recipe order
KFaceEdgeMatch: TypeAlias = tuple[int, tuple[int, int]]


# all recipe edges and endpoint operands must address the boundary of the same named face
def JoinFaceRim(
    Edges: dict[int, AsmPrismEdge],
    Names: dict[str, int],
    Boundary: frozenset[KEdgeNames],
) -> dict[KEdgeNames, KFaceEdgeMatch]:
    EdgeKeys, VertexKeys = ReadIncidence(Edges)
    Matched: dict[KEdgeNames, KFaceEdgeMatch] = {}
    UsedEdges: set[int] = set()
    for FaceNames, VertexNames in Boundary:
        AllNames = FaceNames + tuple(
            NameValue for Group in VertexNames for NameValue in Group
        )
        if any(NameValue not in Names for NameValue in AllNames):
            raise ValueError("Fusion face recipe names are absent on the prior body")
        EdgeId = EdgeKeys.get(frozenset(Names[NameValue] for NameValue in FaceNames))
        if EdgeId is None or EdgeId in UsedEdges:
            raise ValueError("Fusion face recipe requires a unique adjacent face pair")
        First, Second = tuple(
            VertexKeys.get(frozenset(Names[NameValue] for NameValue in Group))
            for Group in VertexNames
        )
        if (
            First is None
            or Second is None
            or {First, Second} != set(Edges[EdgeId].Vertices)
        ):
            raise ValueError("Fusion face recipe endpoint incidence disagrees")
        UsedEdges.add(EdgeId)
        Matched[(FaceNames, VertexNames)] = (EdgeId, (First, Second))
    return Matched
