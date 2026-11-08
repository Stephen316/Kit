# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass
from math import cos as Cosine, hypot as Hypot, sin as SineValue, tau as TauValue
from typing import cast as CastValue

from convert.adapters.freecad.EditShape.CylinderRims import (
    IsNearPoint,
    KAngleTolerance,
    KPositionTolerance,
)
from convert.geometry.Opencascade import LocationPoint
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.surfaces.BrepSurfaces import (
    BrepSurface,
    CylinderSurface,
    PlaneSurface,
)
from interchange.geometry.models.VectorSpace import SpaceVector


# plane and cylinder pcurves only require two verified analytic curve families
@MakeDataClass(frozen=True, slots=True)
class TrimCurve:
    Center: tuple[float, float]
    Direction: tuple[float, float]
    SideVector: tuple[float, float] | None = None
    Radius: float = 0.0


# the native decoder stores the source surface basis before resolving world locations
def SurfaceSide(Surface: BrepSurface) -> SpaceVector:
    Components = CastValue(
        tuple[float, float, float], Surface.attributes["reference_y"]
    )
    return SpaceVector(*Components)


# signed surface bases determine outward orientation independently of carrier axes
def SurfaceHand(Surface: BrepSurface) -> int:
    if isinstance(Surface, PlaneSurface):
        AxisValue = Surface.normal
    elif isinstance(Surface, CylinderSurface):
        AxisValue = Surface.axis
    else:
        return 0
    Handedness = DotVector(
        CrossVector(AxisValue, Surface.reference_direction), SurfaceSide(Surface)
    )
    return -1 if Handedness < 0.0 else 1


# a rim or generator must use the exact analytic parameter speed on the cylinder
def IsTrimFamily(
    Surface: CylinderSurface | PlaneSurface,
    Curve: CircleCurve | LineCurve,
    Trims: tuple[TrimCurve, ...],
) -> bool:
    if isinstance(Surface, PlaneSurface):
        return (
            isinstance(Curve, CircleCurve)
            and len(Trims) == 1
            and Trims[0].SideVector is not None
        )
    if any(Value.SideVector is not None for Value in Trims):
        return False
    if isinstance(Curve, CircleCurve):
        return (
            len(Trims) == 1
            and abs(abs(Trims[0].Direction[0]) - 1.0) <= KAngleTolerance
            and abs(Trims[0].Direction[1]) <= KAngleTolerance
        )
    if len(Trims) != 2:
        return False
    First, Second = Trims
    return (
        all(abs(Value.Direction[0]) <= KAngleTolerance for Value in Trims)
        and abs(abs(First.Direction[1]) - 1.0) <= KAngleTolerance
        and abs(First.Direction[1] - Second.Direction[1]) <= KAngleTolerance
        and abs(abs(First.Center[0] - Second.Center[0]) - TauValue) <= KAngleTolerance
        and abs(First.Center[1] - Second.Center[1]) <= KPositionTolerance
    )


# exact pcurve families permit positional comparisons without curve sampling ambiguity
def TrimPoint(TrimValue: TrimCurve, Parameter: float) -> tuple[float, float]:
    if TrimValue.SideVector is None:
        return (
            TrimValue.Center[0] + TrimValue.Direction[0] * Parameter,
            TrimValue.Center[1] + TrimValue.Direction[1] * Parameter,
        )
    return (
        TrimValue.Center[0]
        + TrimValue.Radius
        * (
            TrimValue.Direction[0] * Cosine(Parameter)
            + TrimValue.SideVector[0] * SineValue(Parameter)
        ),
        TrimValue.Center[1]
        + TrimValue.Radius
        * (
            TrimValue.Direction[1] * Cosine(Parameter)
            + TrimValue.SideVector[1] * SineValue(Parameter)
        ),
    )


# parameter agreement distinguishes a complete wrap from a visually similar carrier
def IsTrimAligned(
    TrimValue: TrimCurve,
    Surface: CylinderSurface | PlaneSurface,
    Curve: CircleCurve | LineCurve,
    SurfacePlace: tuple[float, ...],
    CurvePlace: tuple[float, ...],
    Lower: float,
    Upper: float,
) -> bool:
    SideVector = SurfaceSide(Surface)
    for Fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        Parameter = Lower + (Upper - Lower) * Fraction
        UValue, VValue = TrimPoint(TrimValue, Parameter)
        if isinstance(Surface, CylinderSurface):
            SurfPoint = OffsetVector(
                OffsetVector(
                    OffsetVector(Surface.origin, Surface.axis, VValue),
                    Surface.reference_direction,
                    Surface.radius * Cosine(UValue),
                ),
                SideVector,
                Surface.radius * SineValue(UValue),
            )
        else:
            SurfPoint = OffsetVector(
                OffsetVector(Surface.origin, Surface.reference_direction, UValue),
                SideVector,
                VValue,
            )
        if isinstance(Curve, CircleCurve):
            CurvePoint = OffsetVector(
                OffsetVector(
                    Curve.center,
                    Curve.reference_direction,
                    Curve.radius * Cosine(Parameter),
                ),
                CrossVector(Curve.axis, Curve.reference_direction),
                Curve.radius * SineValue(Parameter),
            )
        else:
            CurvePoint = OffsetVector(Curve.origin, Curve.direction, Parameter)
        if not IsNearPoint(
            LocationPoint(SurfacePlace, SurfPoint),
            LocationPoint(CurvePlace, CurvePoint),
        ):
            return False
    return True


# two dimensional analytic bases must be unit vectors before geometric corroboration
def IsUnitPair(Direction: tuple[float, float]) -> bool:
    return abs(Hypot(*Direction) - 1.0) <= KAngleTolerance
