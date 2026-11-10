# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from pytest import raises as Raises

from convert.formats.Fusion.Revolves.MeridianCoords import CleanMeridian
from convert.formats.Fusion.Revolves.MeridianSense import ChooseMeridian
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# a whole circular profile needs clearance and preserves the same effective axis on reversal
def TestCircleSense() -> None:
    Frame = Transform()
    Origin = SpaceVector(0.0, 0.0, 0.0)
    Center = (PlaneVector(10.0, 0.0),)
    for Direction in (SpaceVector(0.0, 1.0, 0.0), SpaceVector(0.0, -1.0, 0.0)):
        AxisValue, Radial = ChooseMeridian(Frame, Center, Origin, Direction, 2.0)
        assert AxisValue == (0.0, -1.0, 0.0)
        assert Radial == (1.0, 0.0, 0.0)
        with Raises(ValueError, match="crosses or lies on"):
            _ = ChooseMeridian(Frame, Center, Origin, Direction, 10.0)


# only adjacent differences within projection roundoff can share a meridian level
def TestLevelNoise() -> None:
    Projected = ((8.0, 0.0), (8.0 + 2e-15, 10.0), (9.00001, 10.0), (9.0, 1e-15))
    assert CleanMeridian(Projected, 1e-14) == (
        (8.0, 1e-15),
        (8.0, 10.0),
        (9.00001, 10.0),
        (9.0, 1e-15),
    )
