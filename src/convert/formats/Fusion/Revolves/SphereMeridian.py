# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from math import dist as Distance, ulp as UnitPlace

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
    First, Middle, LastValue = (
        EvalArcPoint(ArcValue, Angle)
        for Angle in (Start, (Start + EndValue) * 0.5, EndValue)
    )
    Effective, Radial = ChooseMeridian(
        FrameValue, (First, Middle, LastValue), AxisOrigin, AxisDirection
    )
    Direction = SpaceVector(*Effective)
    AxisPoints: list[SpaceVector] = []
    for Local in (ArcValue.center, First, LastValue):
        World = OffsetVector(
            OffsetVector(FrameValue.origin, FrameValue.x_axis, Local.x),
            FrameValue.y_axis,
            Local.y,
        )
        Offset = OffsetVector(World, AxisOrigin, -1.0)
        OnAxis = OffsetVector(AxisOrigin, Direction, DotVector(Offset, Direction))
        WorldCoords = (World.x, World.y, World.z)
        AxisCoords = (OnAxis.x, OnAxis.y, OnAxis.z)
        Tolerance = max(
            1e-8, 8.0 * UnitPlace(max(map(abs, (*WorldCoords, *AxisCoords))))
        )
        if not Distance(WorldCoords, AxisCoords) <= Tolerance:
            raise ValueError("Fusion semicircle diameter is outside the Revolve axis")
        AxisPoints.append(OnAxis)
    return AxisPoints[0], Direction, SpaceVector(*Radial)
