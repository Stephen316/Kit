from collections import Counter
from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.formats.Fusion.TSplineCodec.Validation.CheckIndices import CheckIndices

KValenceLimit = 8


def CheckVertices(Topology: CageTopology) -> None:
    Counts = Counter(LinkValue.VertexIndex for LinkValue in Topology.Links)
    for Index, Vertex in enumerate(Topology.Vertices):
        CheckIndices((Vertex.OriginLink,), len(Topology.Links), "vertex root")
        if Vertex.Direction not in ("NORTH", "SOUTH", "EAST", "WEST"):
            raise ValueError("Unsupported TSM vertex orientation")
        Current = Vertex.OriginLink
        Visited: set[int] = set()
        while Current not in Visited:
            Visited.add(Current)
            if Topology.Links[Current].VertexIndex != Index:
                raise ValueError("TSM vertex ring crosses ownership")
            Current = Topology.Links[Topology.Links[Current].Opposite].NextLink
        if (
            Current != Vertex.OriginLink
            or len(Visited) != Counts[Index]
            or not 2 <= len(Visited) <= KValenceLimit
        ):
            raise ValueError("Unsupported TSM vertex valence or disconnected fan")
