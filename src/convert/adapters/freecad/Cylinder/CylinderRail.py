# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import hypot as Hypot

from convert.adapters.freecad.Cylinder.CylinderFrame import (
    CylinderGap,
    KAxisTolerance,
    ProjectCylinder,
    NormCylinder,
    RuledRadius,
)
from convert.adapters.freecad.Cylinder.CylinderSpan import CylinderSpan
from convert.geometry.Revolve.SweepVector import CrossVector, OffsetVector
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.surfaces.BrepSurfaces import ConeSurface, CylinderSurface
from interchange.geometry.models.Transform import KOriginZero
from interchange.geometry.models.VectorSpace import SpaceVector


# a generator remains on the carrier at one angular coordinate for its entire span
def ReadCylRail(
    Curve: LineCurve,
    Surface: CylinderSurface | ConeSurface,
    AxisValue: SpaceVector,
    Params: tuple[float, float],
    Vertices: tuple[SpaceVector, SpaceVector],
    Allowed: float,
) -> CylinderSpan | None:
    Direction = NormCylinder(Curve.direction)
    if Direction is None:
        return None
    AxisCross = CrossVector(Direction, AxisValue)
    if (
        isinstance(Surface, CylinderSurface)
        and Hypot(AxisCross.x, AxisCross.y, AxisCross.z) > KAxisTolerance
    ):
        return None
    Points = tuple(
        OffsetVector(Curve.origin, Curve.direction, Param) for Param in Params
    )
    if any(
        not CylinderGap(PointValue, Vertex) <= Allowed
        for PointValue, Vertex in zip(Points, Vertices)
    ):
        return None
    Start, FirstRadial = ProjectCylinder(Points[0], Surface.origin, AxisValue)
    Finish, LastRadial = ProjectCylinder(Points[1], Surface.origin, AxisValue)
    FirstRadius = RuledRadius(Surface, Start)
    LastRadius = RuledRadius(Surface, Finish)
    if (
        not abs(Start - Finish) > Allowed
        or not min(FirstRadius, LastRadius) > 0.0
        or not CylinderGap(
            OffsetVector(KOriginZero, FirstRadial, LastRadius / FirstRadius), LastRadial
        )
        <= Allowed
        or any(
            not abs(Hypot(Radial.x, Radial.y, Radial.z) - Radius) <= Allowed
            for Radial, Radius in ((FirstRadial, FirstRadius), (LastRadial, LastRadius))
        )
    ):
        return None
    return CylinderSpan(Start, Finish, FirstRadial, LastRadial, 0.0)
