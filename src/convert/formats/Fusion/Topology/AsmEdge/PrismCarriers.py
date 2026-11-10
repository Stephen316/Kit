# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from math import dist as Distance, hypot as Hypot, isfinite as IsFinite

from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmNum,
    ReadAsmPtr,
    ReadAsmVec,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmPoints import (
    AsmPointMm,
    IsAsmNear,
    KAsmMatchTol,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.geometry.models.VectorSpace import SpaceVector

# the supported carriers have no attribute pattern or stored entity identity
KPrismCarrier = ((12, -1), (4, -1), (12, -1))


# affine caches retain the original parameter scale and finite edge endpoint interval
def CheckPrismLine(
    Table: AsmTable, EdgeValue: AsmPrismEdge, Points: dict[int, SpaceVector]
) -> None:
    Record = RequireAsm(Table, EdgeValue.Identity, "edge", 11)
    Curve = RequireAsm(Table, ReadAsmPtr(Record, 8), "straight-curve")
    if len(Curve.Tokens) not in (7, 9) or Curve.Tokens[:3] != KPrismCarrier:
        raise ValueError("Unsupported Fusion ASM prism line carrier")
    Lower, Upper = ReadAsmNum(Record, 4), ReadAsmNum(Record, 6)
    if len(Curve.Tokens) == 7:
        if IsAsmFlag(Curve, 5) or IsAsmFlag(Curve, 6):
            raise ValueError("Unsupported Fusion ASM unbounded line flags")
    elif (
        not IsAsmFlag(Curve, 5)
        or not IsAsmFlag(Curve, 7)
        or ReadAsmNum(Curve, 6) != Lower
        or ReadAsmNum(Curve, 8) != Upper
    ):
        raise ValueError("Fusion ASM prism line bounds disagree with its edge")
    Origin = ReadAsmVec(Curve, 3, 19)
    Direction = ReadAsmVec(Curve, 4, 20)
    Length = Hypot(Direction.x, Direction.y, Direction.z)
    if not IsFinite(Length) or Length <= 0.0 or not Lower < Upper:
        raise ValueError("Fusion ASM prism line is degenerate")
    if any(
        not IsAsmNear(
            AsmPointMm(OffsetVector(Origin, Direction, Parameter)), Points[Identity]
        )
        for Identity, Parameter in zip(EdgeValue.Vertices, (Lower, Upper), strict=True)
    ):
        raise ValueError("Fusion ASM prism line disagrees with its named vertices")


# the cache plane equation corroborates the derived carrier independently of face winding
def CheckPrismPlane(Table: AsmTable, FaceId: int, Expected: PlaneSurface) -> None:
    FaceValue = RequireAsm(Table, FaceId, "face", 10)
    PlaneValue = RequireAsm(Table, ReadAsmPtr(FaceValue, 7), "plane-surface", 11)
    if PlaneValue.Tokens[:3] != KPrismCarrier or any(
        IsAsmFlag(PlaneValue, Index) for Index in range(6, 11)
    ):
        raise ValueError("Unsupported Fusion ASM prism plane carrier")
    Origin = AsmPointMm(ReadAsmVec(PlaneValue, 3, 19))
    Normal = ReadAsmVec(PlaneValue, 4, 20)
    Basis = ReadAsmVec(PlaneValue, 5, 20)
    Length = Hypot(Basis.x, Basis.y, Basis.z)
    SignValue = 1.0 if DotVector(Normal, Expected.normal) > 0.0 else -1.0
    Alignment = Distance(
        (Normal.x, Normal.y, Normal.z),
        (
            SignValue * Expected.normal.x,
            SignValue * Expected.normal.y,
            SignValue * Expected.normal.z,
        ),
    )
    if (
        not IsFinite(Length)
        or Length <= 0.0
        or not abs(DotVector(Normal, Basis) / Length) <= 1e-9
        or not Alignment <= 1e-9
        or not abs(
            DotVector(Expected.normal, OffsetVector(Origin, Expected.origin, -1.0))
        )
        <= KAsmMatchTol
    ):
        raise ValueError("Fusion ASM prism plane disagrees with its derived carrier")
