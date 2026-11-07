# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot, isclose as IsClose, isfinite as IsFinite
from operator import mul as Mul, sub as Sub

from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# the occupied sketch half plane fixes the orientation of positive revolution
def CalcMeridian(
    SketchFrame: Transform,
    ProfileLines: tuple[LineGeometry, ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if len(ProfileLines) != 4:
        raise ValueError("Plane limited Fusion Revolve requires a four line profile")
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
        Distance + RadialX * Point.x + RadialY * Point.y
        for LineValue in ProfileLines
        for Point in (LineValue.start, LineValue.end)
    )
    if not all(map(IsFinite, Radii)):
        raise ValueError("Non-finite Fusion Revolve profile radius")
    if min(Radii) >= -1e-8 and max(Radii) > 1e-8:
        return AxisTuple, Radial
    if max(Radii) <= 1e-8 and min(Radii) < -1e-8:
        return (-AxisX, -AxisY, -AxisZ), tuple(-Value for Value in Radial)
    raise ValueError("Fusion Revolve profile crosses or lies on the axis")
