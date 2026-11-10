# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.topology.BrepTopology import BrepEdge, BrepVertex
from interchange.geometry.models.Transform import Transform


# angular trims keep each orbit bounded to the source sweep interval
def BuildArcs(
    Prefix: str,
    Meridian: tuple[tuple[float, float], ...],
    Frame: Transform,
    StartVertices: tuple[BrepVertex, ...],
    EndVertices: tuple[BrepVertex, ...],
    StartRadians: float,
    EndRadians: float,
) -> tuple[tuple[CircleCurve, ...], tuple[BrepEdge | None, ...]]:
    Curves: list[CircleCurve] = []
    Edges: list[BrepEdge | None] = []
    for Index, (Radius, Height) in enumerate(Meridian):
        if Radius == 0.0:
            Edges.append(None)
            continue
        if StartVertices[Index].point == EndVertices[Index].point:
            raise ValueError("Revolve arc endpoints collapse in the spatial frame")
        CurveId = f"{Prefix}-curve-{Index}"
        Curves.append(
            CircleCurve(
                CurveId,
                OffsetVector(Frame.origin, Frame.z_axis, Height),
                Frame.z_axis,
                Frame.x_axis,
                Radius,
            )
        )
        Edges.append(
            BrepEdge(
                f"{Prefix}-edge-{Index}",
                StartVertices[Index].id,
                EndVertices[Index].id,
                CurveId,
                StartRadians,
                EndRadians,
            )
        )
    return tuple(Curves), tuple(Edges)
