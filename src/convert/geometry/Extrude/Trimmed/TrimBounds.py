# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isfinite as IsFinite

from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from convert.geometry.Extrude.Trimmed.TrimOperand import TrimOperand
from convert.geometry.Revolve.SweepBounds import AngularBounds
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# spatial arc extrema depend on the frame axes as well as the angular window
def GetRimBounds(
    PartValue: TrimOperand, FrameValue: Transform, Height: float
) -> tuple[tuple[float, float], ...]:
    Geometry = PartValue.Geometry
    if not isinstance(Geometry, ArcGeometry):
        First = PlacePrismPoint(FrameValue, PartValue.Start, Height)
        Second = PlacePrismPoint(FrameValue, PartValue.Finish, Height)
        return tuple(
            (min(Start, Finish), max(Start, Finish))
            for Start, Finish in zip(
                (First.x, First.y, First.z), (Second.x, Second.y, Second.z)
            )
        )
    Center = PlacePrismPoint(FrameValue, Geometry.center, Height)
    AxisX, AxisY = FrameValue.x_axis, FrameValue.y_axis
    Bounds: list[tuple[float, float]] = []
    for Coordinate, CoeffX, CoeffY in zip(
        (Center.x, Center.y, Center.z),
        (AxisX.x, AxisX.y, AxisX.z),
        (AxisY.x, AxisY.y, AxisY.z),
    ):
        Lower, Upper = AngularBounds(
            CoeffX, CoeffY, Geometry.start_angle, Geometry.end_angle
        )
        Bounds.append(
            (Coordinate + Lower * Geometry.radius, Coordinate + Upper * Geometry.radius)
        )
    return tuple(Bounds)


# linear translation reaches each cartesian extreme on one of the two rim stations
def GetTrimBounds(
    Parts: tuple[TrimOperand, ...],
    FrameValue: Transform,
    LowerMm: float,
    UpperMm: float,
) -> BoundingBox:
    Bounds = tuple(
        GetRimBounds(PartValue, FrameValue, Height)
        for Height in (LowerMm, UpperMm)
        for PartValue in Parts
    )
    if not all(
        IsFinite(Value)
        for RimBounds in Bounds
        for LimitPair in RimBounds
        for Value in LimitPair
    ):
        raise ValueError("Extrude trim spatial bounds exceed floating range")
    return BoundingBox(
        SpaceVector(
            *(min(RimBounds[Index][0] for RimBounds in Bounds) for Index in range(3))
        ),
        SpaceVector(
            *(max(RimBounds[Index][1] for RimBounds in Bounds) for Index in range(3))
        ),
    )
