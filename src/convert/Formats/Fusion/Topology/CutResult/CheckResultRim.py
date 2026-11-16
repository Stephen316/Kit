from math import isclose as IsClose

from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmPtr,
    ReadAsmVec,
    RequireAsm,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmPoints import AsmPointMm, KAsmMatchTol
from convert.Formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from convert.Formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from convert.Formats.Fusion.Topology.AsmEdge.PrismCarriers import KPrismCarrier
from convert.Geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# each connected face loop must lie on its own saved analytic plane
def CheckResultRim(
    Table: AsmTable,
    RingValue: tuple[AsmUse, ...],
    Edges: dict[int, AsmPrismEdge],
    Points: dict[int, SpaceVector],
) -> SpaceVector:
    FaceValue = RequireAsm(Table, RingValue[0].FaceId, "face", 10)
    Plane = RequireAsm(Table, ReadAsmPtr(FaceValue, 7), "plane-surface", 11)
    if Plane.Tokens[:3] != KPrismCarrier or any(
        IsAsmFlag(Plane, Index) for Index in range(6, 11)
    ):
        raise ValueError("Unsupported Fusion Cut result plane framing")
    Origin = AsmPointMm(ReadAsmVec(Plane, 3, 19))
    Normal = ReadAsmVec(Plane, 4, 20)
    if not IsClose(DotVector(Normal, Normal), 1.0, abs_tol=1e-9, rel_tol=0.0):
        raise ValueError("Fusion Cut result plane normal is not a unit vector")
    if any(
        abs(DotVector(Normal, OffsetVector(Points[VertexId], Origin, -1.0)))
        > KAsmMatchTol
        for UseValue in RingValue
        for VertexId in Edges[UseValue.EdgeId].Vertices
    ):
        raise ValueError("Fusion Cut result loop is outside its saved plane")
    return Normal
