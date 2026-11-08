# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot, isfinite as IsFinite

from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.topology.BrepTopology import BrepEdge, BrepVertex
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# shared rim vertices let the cap and adjacent swept faces meet exactly
def BuildRim(
    Prefix: str,
    Meridian: tuple[tuple[float, float], ...],
    Frame: Transform,
    Radial: SpaceVector,
    SharedAxis: tuple[tuple[BrepVertex, ...], tuple[BrepEdge, ...]] | None = None,
) -> tuple[tuple[BrepVertex, ...], tuple[LineCurve, ...], tuple[BrepEdge, ...]]:
    Vertices = tuple(
        (
            SharedAxis[0][Index]
            if SharedAxis is not None and Radius == 0.0
            else BrepVertex(
                f"{Prefix}-vertex-{Index}",
                OffsetVector(
                    OffsetVector(Frame.origin, Frame.z_axis, Height), Radial, Radius
                ),
            )
        )
        for Index, (Radius, Height) in enumerate(Meridian)
    )
    Curves: list[LineCurve] = []
    Edges: list[BrepEdge] = []
    for Index, First in enumerate(Vertices):
        Following = (Index + 1) % len(Vertices)
        if (
            SharedAxis is not None
            and Meridian[Index][0] == Meridian[Following][0] == 0.0
        ):
            Edges.append(SharedAxis[1][Index])
            continue
        Second = Vertices[Following]
        DeltaX = Second.point.x - First.point.x
        DeltaY = Second.point.y - First.point.y
        DeltaZ = Second.point.z - First.point.z
        Length = Hypot(DeltaX, DeltaY, DeltaZ)
        if not IsFinite(Length) or Length == 0.0:
            raise ValueError("Revolve meridian edge collapses in the spatial frame")
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
