from math import isclose as IsClose

from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import IsAsmFlag, RequireAsm
from convert.Formats.Fusion.Topology.AsmEdge.AsmPoints import KAsmMatchTol
from convert.Formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from convert.Formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from convert.Formats.Fusion.Topology.CutResult.CutMetricBox import AxisValues
from convert.Formats.Fusion.Topology.CutResult.CutMetricLoop import CutMetricLoop
from convert.Geometry.Revolve.SweepVector import CrossVector, OffsetVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# full corner membership also needs perimeter order and consistent native orientation
def CheckLoopWinds(
    Shape: CutMetricLoop,
    Corners: tuple[SpaceVector, ...],
    FaceNormal: SpaceVector,
    ReversedFace: bool,
) -> None:
    Segments = tuple(
        OffsetVector(Finish, Start, -1.0)
        for Start, Finish in zip(Corners, Corners[1:] + Corners[:1], strict=True)
    )
    if any(
        sum(abs(Value) > KAsmMatchTol for Value in AxisValues(EdgeValue)) != 1
        for EdgeValue in Segments
    ):
        raise ValueError("Fusion Cut mass loop contains a crossed or degenerate edge")
    RingSense = AxisValues(CrossVector(Segments[0], Segments[1]))[Shape.AxisIndex]
    FaceSense = AxisValues(FaceNormal)[Shape.AxisIndex] * (-1 if ReversedFace else 1)
    if RingSense * Shape.RingSense() <= KAsmMatchTol**2 or not IsClose(
        FaceSense, Shape.FaceSense(), rel_tol=0.0, abs_tol=1e-9
    ):
        raise ValueError("Fusion Cut mass loop or saved face orientation disagrees")


# associate hole and rim loops by their shared native face incidence
def CheckMetricLoop(
    Table: AsmTable,
    Loops: tuple[tuple[AsmUse, ...], ...],
    Edges: dict[int, AsmPrismEdge],
    Points: dict[int, SpaceVector],
    Normals: dict[int, SpaceVector],
    Expected: dict[frozenset[int], CutMetricLoop],
) -> None:
    FaceGroups: dict[int, tuple[int, bool, bool]] = {}
    Checked: set[frozenset[int]] = set()
    for RingValue in Loops:
        Vertices = tuple(
            Edges[UseValue.EdgeId].Vertices[int(UseValue.Reverse)]
            for UseValue in RingValue
        )
        Identity = frozenset(Vertices)
        Shape = Expected.get(Identity)
        if Shape is None or Identity in Checked:
            raise ValueError("Fusion Cut mass contains an unexpected rectangle")
        Checked.add(Identity)
        FaceId = RingValue[0].FaceId
        Group = Shape.FaceGroup()
        if FaceGroups.setdefault(FaceId, Group) != Group:
            raise ValueError(
                "Fusion Cut mass hole and outer loop have different owners"
            )
        FaceValue = RequireAsm(Table, FaceId, "face", 10)
        CheckLoopWinds(
            Shape,
            tuple(Points[Vertex] for Vertex in Vertices),
            Normals[FaceId],
            IsAsmFlag(FaceValue, 8),
        )
    if Checked != set(Expected) or len(set(FaceGroups.values())) != len(FaceGroups):
        raise ValueError("Fusion Cut mass lacks the exact box and opening incidence")
