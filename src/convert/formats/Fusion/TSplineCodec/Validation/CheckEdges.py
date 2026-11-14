from collections import Counter
from math import isfinite
from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.formats.Fusion.TSplineCodec.Validation.CheckIndices import CheckIndices


def CheckEdges(Topology: CageTopology) -> None:
    Counts = Counter(LinkValue.EdgeIndex for LinkValue in Topology.Links)
    for Index, EdgeValue in enumerate(Topology.Edges):
        CheckIndices((EdgeValue.OriginLink,), len(Topology.Links), "edge root")
        if (
            Topology.Links[EdgeValue.OriginLink].EdgeIndex != Index
            or Counts[Index] != 2
        ):
            raise ValueError("TSM edge ownership differs")
        if not isfinite(EdgeValue.KnotInterval) or EdgeValue.KnotInterval <= 0.0:
            raise ValueError("Unsupported TSM knot interval")
    Boundary = {
        LinkValue.EdgeIndex for LinkValue in Topology.Links if LinkValue.FaceIndex == -1
    }
    Indices = tuple(Condition.EdgeIndex for Condition in Topology.EndConditions)
    CheckIndices(Indices, len(Topology.Edges), "end-condition edge")
    if set(Indices) != Boundary or any(
        Condition.EndValue != 0.0 for Condition in Topology.EndConditions
    ):
        raise ValueError("Unsupported TSM edge end conditions")
