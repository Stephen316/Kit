# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import dist as Dist, ulp as Ulp

from convert.formats.Fusion.Profiles.ArcRing import EvalArcPoint
from convert.formats.Fusion.Revolves.MeridianSense import ChooseMeridian
from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# the diameter must coincide with the axis before a semicircle can produce a sphere
def ReadSphereAxis(
    FrameValue: Transform,
    ArcValue: ArcGeometry,
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
) -> tuple[SpaceVector, SpaceVector, SpaceVector]:
    Start, EndValue = ArcValue.start_angle, ArcValue.end_angle
    First, Middle, Last = (
        EvalArcPoint(ArcValue, Angle)
        for Angle in (Start, (Start + EndValue) * 0.5, EndValue)
    )
    Effective, Radial = ChooseMeridian(
        FrameValue, (First, Middle, Last), AxisOrigin, AxisDirection
    )
    Direction = SpaceVector(*Effective)
    AxisPoints = []
    for Local in (ArcValue.center, First, Last):
        World = OffsetVector(
            OffsetVector(FrameValue.origin, FrameValue.x_axis, Local.x),
            FrameValue.y_axis,
            Local.y,
        )
        Offset = OffsetVector(World, AxisOrigin, -1.0)
        OnAxis = OffsetVector(AxisOrigin, Direction, DotVector(Offset, Direction))
        WorldCoords = (World.x, World.y, World.z)
        AxisCoords = (OnAxis.x, OnAxis.y, OnAxis.z)
        Tolerance = max(1e-8, 8.0 * Ulp(max(map(abs, (*WorldCoords, *AxisCoords)))))
        if not Dist(WorldCoords, AxisCoords) <= Tolerance:
            raise ValueError("Fusion semicircle diameter is outside the Revolve axis")
        AxisPoints.append(OnAxis)
    return AxisPoints[0], Direction, SpaceVector(*Radial)
