# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import cos as Cosine, pi as PiValue, sin as SineValue

from convert.adapters.freecad.EditShape.CylinderRims import KAngleTolerance
from convert.geometry.Opencascade import (
    DecodeFailure,
    IsFrame,
    ReadCount,
    Tokens,
    VectorValue,
)
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.surfaces.BrepSurfaces import (
    ConeSurface,
    CylinderSurface,
    PlaneSurface,
)
from interchange.geometry.models.VectorSpace import SpaceVector

# only elementary sweep carriers are qualified by the native shape witness
KRevCurve = LineCurve | CircleCurve

# the surface family fixes which exact native parameterization is allowed
KRevSurface = PlaneSurface | CylinderSurface | ConeSurface


# stored basis parity determines the orientation of the native surface derivatives
def ReadRevSurface(Cursor: Tokens, Index: int) -> KRevSurface:
    Family = Cursor.ReadInteger(1, 3)
    Origin, AxisValue, RefValue, SideValue = (VectorValue(Cursor) for _ in range(4))
    if not IsFrame(AxisValue, RefValue, SideValue):
        raise DecodeFailure("invalid Revolution surface frame")
    NameValue = f"revolution:surface:{Index}"
    Attrs = {"reference_y": (SideValue.x, SideValue.y, SideValue.z)}
    if Family == 1:
        return PlaneSurface(NameValue, Origin, AxisValue, RefValue, attributes=Attrs)
    Radius = Cursor.ReadNumber()
    if Radius <= 0.0:
        raise DecodeFailure("invalid Revolution surface radius")
    if Family == 2:
        return CylinderSurface(
            NameValue, Origin, AxisValue, RefValue, Radius, attributes=Attrs
        )
    HalfAngle = Cursor.ReadNumber()
    if not KAngleTolerance < abs(HalfAngle) < PiValue / 2.0 - KAngleTolerance:
        raise DecodeFailure("invalid Revolution cone angle")
    return ConeSurface(
        NameValue, Origin, AxisValue, RefValue, Radius, HalfAngle, attributes=Attrs
    )


# checking circle handedness keeps its evaluated direction bound to the original frame
def CheckCurveAxes(Cursor: Tokens, Maximum: int) -> None:
    Count = ReadCount(Cursor, b"Curves", Maximum)
    for _ in range(Count):
        Family = Cursor.ReadInteger(1, 2)
        _ = VectorValue(Cursor)
        AxisValue = VectorValue(Cursor)
        if Family == 2:
            First, Second = VectorValue(Cursor), VectorValue(Cursor)
            _ = Cursor.ReadNumber()
            if DotVector(CrossVector(AxisValue, First), Second) < 1.0 - KAngleTolerance:
                raise DecodeFailure("invalid Revolution circle handedness")


# line and circle trims can be verified through their exact analytic parameterizations
def CurvePoint(Curve: KRevCurve, Param: float) -> SpaceVector:
    if isinstance(Curve, LineCurve):
        return OffsetVector(Curve.origin, Curve.direction, Param)
    SideValue = CrossVector(Curve.axis, Curve.reference_direction)
    return OffsetVector(
        OffsetVector(
            Curve.center, Curve.reference_direction, Curve.radius * Cosine(Param)
        ),
        SideValue,
        Curve.radius * SineValue(Param),
    )


# finite cone meridians use slant distance while cylinders use axial distance
def SurfacePoint(
    Surface: KRevSurface, SideValue: SpaceVector, UValue: float, VValue: float
) -> SpaceVector:
    if isinstance(Surface, PlaneSurface):
        return OffsetVector(
            OffsetVector(Surface.origin, Surface.reference_direction, UValue),
            SideValue,
            VValue,
        )
    Radius, Axial = Surface.radius, VValue
    if isinstance(Surface, ConeSurface):
        Radius += VValue * SineValue(Surface.half_angle)
        Axial *= Cosine(Surface.half_angle)
    if Radius <= 0.0:
        raise DecodeFailure("Revolution pcurve crosses the axis")
    return OffsetVector(
        OffsetVector(
            OffsetVector(Surface.origin, Surface.axis, Axial),
            Surface.reference_direction,
            Radius * Cosine(UValue),
        ),
        SideValue,
        Radius * SineValue(UValue),
    )
