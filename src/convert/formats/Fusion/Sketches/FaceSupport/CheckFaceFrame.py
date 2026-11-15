from math import dist as Distance

from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmVec,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmPoints import AsmPointMm, KAsmMatchTol
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from convert.formats.Fusion.Topology.AsmEdge.PrismCarriers import KPrismCarrier
from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# the saved frame corroborates the selected occurrence without using a geometric nearest face match
def CheckFaceFrame(
    Table: AsmTable,
    PlaneIndex: int,
    Frame: Transform,
    Corners: tuple[SpaceVector, ...],
) -> None:
    PlaneValue = RequireAsm(Table, PlaneIndex, "plane-surface", 11)
    if PlaneValue.Tokens[:3] != KPrismCarrier or any(
        IsAsmFlag(PlaneValue, Index) for Index in range(6, 11)
    ):
        raise ValueError("Unsupported Fusion ASM sketch support carrier")
    Normal = ReadAsmVec(PlaneValue, 4, 20)
    AxisX = ReadAsmVec(PlaneValue, 5, 20)
    Origin = AsmPointMm(ReadAsmVec(PlaneValue, 3, 19))
    if any(
        Distance((Actual.x, Actual.y, Actual.z), (Expected.x, Expected.y, Expected.z))
        > 1e-9
        for Actual, Expected in ((Normal, Frame.z_axis), (AxisX, Frame.x_axis))
    ) or any(
        abs(DotVector(Normal, OffsetVector(Point, Origin, -1.0))) > KAsmMatchTol
        for Point in (Frame.origin, *Corners)
    ):
        raise ValueError("Fusion saved support face disagrees with the sketch frame")
