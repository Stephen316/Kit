# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import hypot as Hypot, isclose as IsClose

from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.topology.BrepTopology import BrepEdge, BrepVertex
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# rim and rail edges retain shared endpoints for exact cap and wall connectivity
def BuildPrismEdges(
    Prefix: str,
    FrameValue: Transform,
    Points: tuple[PlaneVector, ...],
    LowerMm: float,
    UpperMm: float,
) -> tuple[tuple[BrepVertex, ...], tuple[LineCurve, ...], tuple[BrepEdge, ...]]:
    Count = len(Points)
    Vertices = tuple(
        BrepVertex(
            f"{Prefix}-vertex-{Station * Count + Index}",
            PlacePrismPoint(FrameValue, PointValue, Height),
        )
        for Station, Height in enumerate((LowerMm, UpperMm))
        for Index, PointValue in enumerate(Points)
    )
    Segments = (
        tuple((Index, (Index + 1) % Count) for Index in range(Count))
        + tuple((Count + Index, Count + (Index + 1) % Count) for Index in range(Count))
        + tuple((Index, Count + Index) for Index in range(Count))
    )
    RimLengths = tuple(
        Hypot(Second.x - First.x, Second.y - First.y)
        for First, Second in zip(Points, Points[1:] + Points[:1])
    )
    Lengths = RimLengths * 2 + (UpperMm - LowerMm,) * Count
    Curves: list[LineCurve] = []
    Edges: list[BrepEdge] = []
    for Index, (Start, Finish) in enumerate(Segments):
        First, Second = Vertices[Start], Vertices[Finish]
        DeltaX = Second.point.x - First.point.x
        DeltaY = Second.point.y - First.point.y
        DeltaZ = Second.point.z - First.point.z
        Length = Hypot(DeltaX, DeltaY, DeltaZ)
        if not IsClose(Length, Lengths[Index], rel_tol=1e-8, abs_tol=0.0):
            raise ValueError("Extrude prism edge loses precision in the spatial frame")
        CurveId = f"{Prefix}-curve-{Index}"
        Curves.append(
            LineCurve(
                CurveId,
                First.point,
                SpaceVector(DeltaX / Length, DeltaY / Length, DeltaZ / Length),
            )
        )
        Edges.append(
            BrepEdge(
                f"{Prefix}-edge-{Index}", First.id, Second.id, CurveId, 0.0, Length
            )
        )
    return Vertices, tuple(Curves), tuple(Edges)
