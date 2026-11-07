# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import pi as Pi

from pytest import raises as Raises

from convert.formats.Fusion.Profiles.ArcRing import CheckSemiRing
from convert.formats.Fusion.Revolves.SphereMeridian import ReadSphereAxis
from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# sphere construction requires a closed semicircle whose diameter is on the axis
def TestSphereAxis() -> None:
    Center = PlaneVector(0.0, 4.0)
    ArcValue = ArcGeometry(Center, 2.0, Pi * 0.5, Pi * 1.5)
    Diameter = LineGeometry(PlaneVector(0.0, 6.0), PlaneVector(0.0, 2.0))
    CheckSemiRing(ArcValue, Diameter)
    CheckSemiRing(ArcValue, LineGeometry(Diameter.end, Diameter.start))
    with Raises(ValueError, match="does not close"):
        CheckSemiRing(ArcValue, LineGeometry(PlaneVector(0.0, 5.0), Diameter.end))
    Axis = SpaceVector(0.0, 1.0, 0.0)
    Origin = SpaceVector(0.0, 0.0, 0.0)
    assert ReadSphereAxis(Transform(), ArcValue, Origin, Axis) == (
        SpaceVector(0.0, 4.0, 0.0),
        Axis,
        SpaceVector(-1.0, 0.0, 0.0),
    )
    with Raises(ValueError, match="diameter is outside"):
        ReadSphereAxis(Transform(), ArcValue, SpaceVector(1.0, 0.0, 0.0), Axis)
