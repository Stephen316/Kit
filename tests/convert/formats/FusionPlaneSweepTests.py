# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import cos as Cosine, radians as Radians, sin as SineValue

from pytest import approx as Approx, raises as Raises

from convert.formats.Fusion.Revolves.PlaneSweep import DerivePlaneSpan
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# ordered limits must survive target swaps and end past the straight angle
def TestPlaneSector() -> None:
    Profile = MakeProfile(10.0)
    Origin = SpaceVector(0.0, 0.0, 0.0)
    Direction = SpaceVector(0.0, 1.0, 0.0)
    Positive, Negative = MakeTarget(45), MakeTarget(-35)
    for Targets, Expected in (
        ((Positive,), (0, 135)),
        ((Negative,), (0, 35)),
        ((Positive, Negative), (135, 215)),
        ((Negative, Positive), (135, 215)),
    ):
        AxisValue, Lower, Upper = DerivePlaneSpan(
            Transform(), Profile, Origin, Direction, Targets
        )
        assert AxisValue == SpaceVector(0.0, -1.0, 0.0)
        assert (Lower, Upper) == Approx(tuple(map(Radians, Expected)))


# both the profile and the limits must qualify in the same meridian frame
def TestSweepGuards() -> None:
    Origin = SpaceVector(0.0, 0.0, 0.0)
    Direction = SpaceVector(0.0, 1.0, 0.0)
    Positive = MakeTarget(45)
    with Raises(ValueError, match="profile crosses"):
        _ = DerivePlaneSpan(
            Transform(), MakeProfile(-10.0), Origin, Direction, (Positive,)
        )
    with Raises(ValueError, match="must contain the axis"):
        _ = DerivePlaneSpan(
            Transform(), MakeProfile(10.0), Origin, Direction, (MakeTarget(45, 1.0),)
        )
    with Raises(ValueError, match="coincide"):
        _ = DerivePlaneSpan(
            Transform(), MakeProfile(10.0), Origin, Direction, (Positive, Positive)
        )
    with Raises(ValueError, match="coincides with the sketch"):
        _ = DerivePlaneSpan(
            Transform(), MakeProfile(10.0), Origin, Direction, (MakeTarget(0),)
        )


# synthetic profiles distinguish occupied half planes without depending on captured bytes
def MakeProfile(FirstX: float) -> tuple[LineGeometry, ...]:
    Corners = (
        PlaneVector(FirstX, 10.0),
        PlaneVector(30.0, 10.0),
        PlaneVector(30.0, 40.0),
        PlaneVector(FirstX, 40.0),
    )
    return tuple(
        LineGeometry(First, Second)
        for First, Second in zip(Corners, Corners[1:] + Corners[:1])
    )


# synthetic target frames separate angular branches from axis incidence
def MakeTarget(Degrees: int, OffsetX: float = 0.0) -> Transform:
    Angle = Radians(Degrees)
    return Transform(
        origin=SpaceVector(OffsetX, 0.0, 0.0),
        x_axis=SpaceVector(0.0, 1.0, 0.0),
        y_axis=SpaceVector(-Cosine(Angle), 0.0, SineValue(Angle)),
        z_axis=SpaceVector(SineValue(Angle), 0.0, Cosine(Angle)),
    )
