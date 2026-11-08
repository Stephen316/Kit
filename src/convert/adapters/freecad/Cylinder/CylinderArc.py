# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import cos as Cos, hypot as Hypot, isfinite as IsFinite
from math import sin as Sin, tau as FullTurn

from convert.adapters.freecad.Cylinder.CylinderFrame import (
    CylinderGap,
    KAxisTolerance,
    ProjectCylinder,
    NormCylinder,
)
from convert.adapters.freecad.Cylinder.CylinderSpan import CylinderSpan
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.surfaces.BrepSurfaces import CylinderSurface
from interchange.geometry.models.VectorSpace import SpaceVector


# a circle trim supplies one horizontal side with a signed unwrapped angular extent
def ReadCylinderArc(
    Curve: CircleCurve,
    Surface: CylinderSurface,
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
    Skew = Hypot(AxisCross.x, AxisCross.y, AxisCross.z)
    _, CenterRadial = ProjectCylinder(Curve.center, Surface.origin, AxisValue)
    Deviation = (
        Hypot(CenterRadial.x, CenterRadial.y, CenterRadial.z)
        + abs(Curve.radius - Surface.radius)
        + Curve.radius * Skew
    )
    Sweep = Params[1] - Params[0]
    if (
        not AngleTol < abs(Sweep) < FullTurn - AngleTol
        or Skew > KAxisTolerance
        or not Deviation <= Allowed
    ):
        return None
    ArcTangent = CrossVector(ArcAxis, ArcRef)
    Points = tuple(
        OffsetVector(
            OffsetVector(Curve.center, ArcRef, Curve.radius * Cos(Param)),
            ArcTangent,
            Curve.radius * Sin(Param),
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
