from math import dist as Distance, isclose as IsClose

from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmNum,
    ReadAsmPtr,
    ReadAsmVec,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.geometry.models.VectorSpace import SpaceVector

# all topology geometry is corroborated in the same bounded source coordinate frame
KAsmMatchTol = 1e-7


# native cache checks use physical separation rather than permissive relative error
def IsAsmNear(First: SpaceVector, Second: SpaceVector) -> bool:
    return (
        Distance((First.x, First.y, First.z), (Second.x, Second.y, Second.z))
        <= KAsmMatchTol
    )


# cached centimetre coordinates need conversion to millimetres independently of archive header units
def AsmPointMm(Value: SpaceVector) -> SpaceVector:
    return SpaceVector(10.0 * Value.x, 10.0 * Value.y, 10.0 * Value.z)


# prism callers retain their source profile cardinality contract
def ReadAsmPoints(
    Table: AsmTable, Edges: dict[int, AsmPrismEdge], Sides: int
) -> dict[int, SpaceVector]:
    return ReadAsmVerts(Table, Edges, 2 * Sides)


# vertex ownership is validated against the graph before reading its stored point
def ReadAsmVerts(
    Table: AsmTable, Edges: dict[int, AsmPrismEdge], VertexCount: int
) -> dict[int, SpaceVector]:
    Incident: dict[int, set[int]] = {}
    for EdgeValue in Edges.values():
        for Identity in EdgeValue.Vertices:
            Incident.setdefault(Identity, set()).add(EdgeValue.Identity)
    if len(Incident) != VertexCount:
        raise ValueError("Fusion ASM vertex inventory disagrees")
    Points: dict[int, SpaceVector] = {}
    for Identity, EdgesAt in Incident.items():
        Value = RequireAsm(Table, Identity, "vertex", 6)
        if len(EdgesAt) != 3 or ReadAsmPtr(Value, 3) not in EdgesAt:
            raise ValueError("Fusion ASM prism vertex edge head disagrees")
        Point = RequireAsm(Table, ReadAsmPtr(Value, 5), "point", 4)
        Points[Identity] = AsmPointMm(ReadAsmVec(Point, 3, 19))
    return Points


# the selected straight curve and finite edge interval corroborate the named endpoints
def CheckAsmLine(
    Table: AsmTable, EdgeValue: AsmPrismEdge, Points: dict[int, SpaceVector]
) -> None:
    Record = RequireAsm(Table, EdgeValue.Identity, "edge", 11)
    Curve = RequireAsm(Table, ReadAsmPtr(Record, 8), "straight-curve", 9)
    Origin = ReadAsmVec(Curve, 3, 19)
    Direction = ReadAsmVec(Curve, 4, 20)
    Lower, Upper = ReadAsmNum(Record, 4), ReadAsmNum(Record, 6)
    if (
        not Lower < Upper
        or not IsAsmFlag(Curve, 5)
        or not IsAsmFlag(Curve, 7)
        or ReadAsmNum(Curve, 6) != Lower
        or ReadAsmNum(Curve, 8) != Upper
        or not IsClose(DotVector(Direction, Direction), 1.0, rel_tol=0.0, abs_tol=1e-9)
        or any(
            not IsAsmNear(
                AsmPointMm(OffsetVector(Origin, Direction, Param)), Points[Identity]
            )
            for Identity, Param in zip(EdgeValue.Vertices, (Lower, Upper), strict=True)
        )
    ):
        raise ValueError(
            "Fusion ASM selected line carrier disagrees with its named vertices"
        )
