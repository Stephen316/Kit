# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import hypot as Hypot, isclose as IsClose, isfinite as IsFinite
from operator import mul as Multiply, sub as Substitute

from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# the occupied sketch half plane fixes the orientation of positive revolution
def ChooseMeridian(
    SketchFrame: Transform,
    ProfilePoints: tuple[PlaneVector, ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
    Clearance: float = 0.0,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if not ProfilePoints or not IsFinite(Clearance) or Clearance < 0.0:
        raise ValueError("Fusion Revolve profile has invalid radial bounds")
    AxisTuple = (AxisDirection.x, AxisDirection.y, AxisDirection.z)
    Normal = (SketchFrame.z_axis.x, SketchFrame.z_axis.y, SketchFrame.z_axis.z)
    FrameOrigin = (SketchFrame.origin.x, SketchFrame.origin.y, SketchFrame.origin.z)
    AxisPoint = (AxisOrigin.x, AxisOrigin.y, AxisOrigin.z)
    Offset = tuple(map(Substitute, FrameOrigin, AxisPoint))
    if (
        not IsClose(Hypot(*AxisTuple), 1.0, rel_tol=0.0, abs_tol=1e-9)
        or not IsClose(Hypot(*Normal), 1.0, rel_tol=0.0, abs_tol=1e-9)
        or not IsClose(sum(map(Multiply, Normal, AxisTuple)), 0.0, abs_tol=1e-9)
        or not IsClose(sum(map(Multiply, Normal, Offset)), 0.0, abs_tol=1e-8)
    ):
        raise ValueError("Fusion Revolve axis is outside the sketch plane")
    AxisX, AxisY, AxisZ = AxisTuple
    NormalX, NormalY, NormalZ = Normal
    Radial = (
        NormalY * AxisZ - NormalZ * AxisY,
        NormalZ * AxisX - NormalX * AxisZ,
        NormalX * AxisY - NormalY * AxisX,
    )
    SketchX = (SketchFrame.x_axis.x, SketchFrame.x_axis.y, SketchFrame.x_axis.z)
    SketchY = (SketchFrame.y_axis.x, SketchFrame.y_axis.y, SketchFrame.y_axis.z)
    Distance, RadialX, RadialY = (
        sum(map(Multiply, Radial, Vector)) for Vector in (Offset, SketchX, SketchY)
    )
    Radii = tuple(
        Distance + RadialX * Point.x + RadialY * Point.y for Point in ProfilePoints
    )
    Sense = ChooseRadial(Radii, Clearance)
    if Sense > 0:
        return AxisTuple, Radial
    return (-AxisX, -AxisY, -AxisZ), (-Radial[0], -Radial[1], -Radial[2])


# the signed profile radii determine which side can safely become the meridian
def ChooseRadial(Radii: tuple[float, ...], Clearance: float) -> int:
    if not all(map(IsFinite, Radii)):
        raise ValueError("Non-finite Fusion Revolve profile radius")
    Minimum, Maximum = min(Radii), max(Radii)
    if Clearance > 0.0:
        Positive = Minimum > Clearance + 1e-8
        Negative = Maximum < -Clearance - 1e-8
    else:
        Positive = Minimum >= -1e-8 and Maximum > 1e-8
        Negative = Maximum <= 1e-8 and Minimum < -1e-8
    if Positive:
        return 1
    if Negative:
        return -1
    raise ValueError("Fusion Revolve profile crosses or lies on the axis")
