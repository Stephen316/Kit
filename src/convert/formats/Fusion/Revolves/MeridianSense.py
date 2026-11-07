# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot, isclose as IsClose, isfinite as IsFinite
from operator import mul as Mul, sub as Sub

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
    Offset = tuple(map(Sub, FrameOrigin, AxisPoint))
    if (
        not IsClose(Hypot(*AxisTuple), 1.0, rel_tol=0.0, abs_tol=1e-9)
        or not IsClose(Hypot(*Normal), 1.0, rel_tol=0.0, abs_tol=1e-9)
        or not IsClose(sum(map(Mul, Normal, AxisTuple)), 0.0, abs_tol=1e-9)
        or not IsClose(sum(map(Mul, Normal, Offset)), 0.0, abs_tol=1e-8)
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
        sum(map(Mul, Radial, Vector)) for Vector in (Offset, SketchX, SketchY)
    )
    Radii = tuple(
        Distance + RadialX * Point.x + RadialY * Point.y for Point in ProfilePoints
    )
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
        return AxisTuple, Radial
    if Negative:
        return (-AxisX, -AxisY, -AxisZ), tuple(-Value for Value in Radial)
    raise ValueError("Fusion Revolve profile crosses or lies on the axis")
