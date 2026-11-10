# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from math import tau as FullTurn

from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import BrepCurve, CircleCurve, LineCurve
from interchange.brep.topology.BrepTopology import BrepEdge, BrepVertex
from interchange.geometry.models.Transform import Transform


# each orbit is periodic and an isolated apex represents a singular cone trim
def BuildFullRings(
    Prefix: str,
    Meridian: tuple[tuple[float, float], ...],
    Frame: Transform,
) -> tuple[tuple[BrepVertex, ...], tuple[BrepCurve, ...], dict[int, BrepEdge]]:
    Vertices: list[BrepVertex] = []
    Curves: list[BrepCurve] = []
    Edges: dict[int, BrepEdge] = {}
    Count = len(Meridian)
    for Index, (Radius, Height) in enumerate(Meridian):
        Before = Meridian[Index - 1]
        After = Meridian[(Index + 1) % Count]
        Singular = Radius == 0.0
        if Singular and not any(
            NearRadius > 0.0 and NearHeight != Height
            for NearRadius, NearHeight in (Before, After)
        ):
            continue
        RingId = f"{Prefix}-orbit-{Index}"
        Center = OffsetVector(Frame.origin, Frame.z_axis, Height)
        Point = OffsetVector(Center, Frame.x_axis, Radius)
        Vertex = BrepVertex(f"{RingId}-vertex", Point)
        CurveId = f"{RingId}-curve"
        if Singular:
            Curves.append(LineCurve(CurveId, Point, Frame.z_axis))
        else:
            Curves.append(
                CircleCurve(CurveId, Center, Frame.z_axis, Frame.x_axis, Radius)
            )
        Edges[Index] = BrepEdge(
            f"{RingId}-edge",
            Vertex.id,
            Vertex.id,
            CurveId,
            0.0,
            0.0 if Singular else FullTurn,
            degenerate=Singular,
        )
        Vertices.append(Vertex)
    return tuple(Vertices), tuple(Curves), Edges
