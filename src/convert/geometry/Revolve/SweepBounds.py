# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import atan2 as AngleOf
from math import cos as Cos
from math import hypot as Hypot
from math import pi as HalfTurn
from math import sin as Sin
from math import tau as FullTurn

from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.VectorSpace import SpaceVector


# angular extrema include stationary points even when the interval crosses zero
def AngularBounds(
    Radial: float, Tangent: float, StartRadians: float, EndRadians: float
) -> tuple[float, float]:
    StartCos = Cos(StartRadians)
    StartSin = Sin(StartRadians)
    StartValue = Radial * StartCos + Tangent * StartSin
    EndValue = Radial * Cos(EndRadians) + Tangent * Sin(EndRadians)
    Amplitude = Hypot(Radial, Tangent)
    RelativePeak = (
        AngleOf(Tangent * StartCos - Radial * StartSin, StartValue) % FullTurn
    )
    Span = EndRadians - StartRadians
    Minimum = min(StartValue, EndValue)
    Maximum = max(StartValue, EndValue)
    if RelativePeak <= Span:
        Maximum = Amplitude
    if (RelativePeak + HalfTurn) % FullTurn <= Span:
        Minimum = -Amplitude
    return Minimum, Maximum


# a positive radius makes each cartesian bound linear over the meridian vertices
def GetSweepBounds(
    Meridian: tuple[tuple[float, float], ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
    StartRadians: float,
    EndRadians: float,
) -> BoundingBox:
    Tangent = (
        AxisDirection.y * Radial.z - AxisDirection.z * Radial.y,
        AxisDirection.z * Radial.x - AxisDirection.x * Radial.z,
        AxisDirection.x * Radial.y - AxisDirection.y * Radial.x,
    )
    Minimum: list[float] = []
    Maximum: list[float] = []
    for Center, Axial, RadiusDir, TangentDir in zip(
        (AxisOrigin.x, AxisOrigin.y, AxisOrigin.z),
        (AxisDirection.x, AxisDirection.y, AxisDirection.z),
        (Radial.x, Radial.y, Radial.z),
        Tangent,
    ):
        Lower, Upper = AngularBounds(RadiusDir, TangentDir, StartRadians, EndRadians)
        Minimum.append(
            Center + min(Axial * Height + Lower * Radius for Radius, Height in Meridian)
        )
        Maximum.append(
            Center + max(Axial * Height + Upper * Radius for Radius, Height in Meridian)
        )
    return BoundingBox(SpaceVector(*Minimum), SpaceVector(*Maximum))
