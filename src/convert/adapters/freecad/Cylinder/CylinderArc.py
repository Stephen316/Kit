# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import cos as Cosine, hypot as Hypot, isfinite as IsFinite
from math import sin as SineValue, tan as Tangent, tau as FullTurn

from convert.adapters.freecad.Cylinder.CylinderFrame import (
    CylinderGap,
    KAxisTolerance,
    ProjectCylinder,
    NormCylinder,
    RuledRadius,
)
from convert.adapters.freecad.Cylinder.CylinderSpan import CylinderSpan
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.surfaces.BrepSurfaces import ConeSurface, CylinderSurface
from interchange.geometry.models.VectorSpace import SpaceVector


# a circle trim supplies one horizontal side with a signed unwrapped angular extent
def ReadCylinderArc(
    Curve: CircleCurve,
    Surface: CylinderSurface | ConeSurface,
    AxisValue: SpaceVector,
    Params: tuple[float, float],
    Vertices: tuple[SpaceVector, SpaceVector],
    Allowed: float,
    AngleTol: float,
) -> CylinderSpan | None:
    ArcAxis = NormCylinder(Curve.axis)
    ArcRef = NormCylinder(Curve.reference_direction)
    if (
        not IsFinite(Curve.radius)
        or Curve.radius <= 0.0
        or ArcAxis is None
        or ArcRef is None
        or abs(DotVector(ArcAxis, ArcRef)) > KAxisTolerance
    ):
        return None
    AxisCross = CrossVector(ArcAxis, AxisValue)
    SkewValue = Hypot(AxisCross.x, AxisCross.y, AxisCross.z)
    Station, CenterRadial = ProjectCylinder(Curve.center, Surface.origin, AxisValue)
    ExpectedRadius = RuledRadius(Surface, Station)
    Slope = (
        abs(Tangent(Surface.half_angle)) if isinstance(Surface, ConeSurface) else 0.0
    )
    Deviation = (
        Hypot(CenterRadial.x, CenterRadial.y, CenterRadial.z)
        + abs(Curve.radius - ExpectedRadius)
        + Curve.radius * SkewValue * (1.0 + Slope)
    )
    Sweep = Params[1] - Params[0]
    if (
        not ExpectedRadius > 0.0
        or not AngleTol < abs(Sweep) < FullTurn - AngleTol
        or SkewValue > KAxisTolerance
        or not Deviation <= Allowed
    ):
        return None
    ArcTangent = CrossVector(ArcAxis, ArcRef)
    Points = tuple(
        OffsetVector(
            OffsetVector(Curve.center, ArcRef, Curve.radius * Cosine(Param)),
            ArcTangent,
            Curve.radius * SineValue(Param),
        )
        for Param in Params
    )
    if any(
        not CylinderGap(PointValue, Vertex) <= Allowed
        for PointValue, Vertex in zip(Points, Vertices)
    ):
        return None
    Start, FirstRadial = ProjectCylinder(Points[0], Surface.origin, AxisValue)
    Finish, LastRadial = ProjectCylinder(Points[1], Surface.origin, AxisValue)
    if not (
        abs(Start - Finish) <= Allowed
        and CylinderGap(FirstRadial, LastRadial) > Allowed
    ):
        return None
    return CylinderSpan(
        Start,
        Finish,
        FirstRadial,
        LastRadial,
        Sweep if DotVector(ArcAxis, AxisValue) > 0.0 else -Sweep,
    )
