# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import dist as Distance, ulp as FloatUlp
from operator import mul as Multiply, sub as Subtract

from convert.formats.Fusion.Revolves.MeridianCoords import CleanMeridian, RadialLevel
from convert.formats.Fusion.Revolves.ProfileMeridian import CalcMeridian
from convert.formats.Fusion.Sketches.SketchPrimitive import IsSamePoint
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# the source curve order establishes a cyclic polygon without altering stored directions
def ReadCorners(Lines: tuple[LineGeometry, ...]) -> tuple[PlaneVector, ...]:
    if len(Lines) < 3:
        raise ValueError("Fusion Revolve needs a closed line profile")
    First, *Remaining = Lines
    Points = [First.start]
    TipValue = First.end
    for LineValue in Remaining:
        Points.append(TipValue)
        if IsSamePoint(LineValue.start, TipValue):
            TipValue = LineValue.end
        elif IsSamePoint(LineValue.end, TipValue):
            TipValue = LineValue.start
        else:
            raise ValueError("Fusion Revolve profile traversal is disconnected")
    if not IsSamePoint(TipValue, First.start):
        raise ValueError("Fusion Revolve profile traversal does not close")
    return tuple(Points)


# the derived solid must start in the same right handed frame as the feature definition
def ReadMeridian(
    SketchFrame: Transform,
    ProfileLines: tuple[LineGeometry, ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
) -> tuple[tuple[tuple[float, float], ...], SpaceVector]:
    AxisTuple, Radial = CalcMeridian(
        SketchFrame, ProfileLines, AxisOrigin, AxisDirection
    )
    if Distance(AxisTuple, (AxisDirection.x, AxisDirection.y, AxisDirection.z)) > 1e-9:
        raise ValueError(
            "Fusion Revolve profile direction disagrees with its definition"
        )
    Offset = tuple(
        map(
            Subtract,
            (SketchFrame.origin.x, SketchFrame.origin.y, SketchFrame.origin.z),
            (AxisOrigin.x, AxisOrigin.y, AxisOrigin.z),
        )
    )
    Basis = (
        Offset,
        (SketchFrame.x_axis.x, SketchFrame.x_axis.y, SketchFrame.x_axis.z),
        (SketchFrame.y_axis.x, SketchFrame.y_axis.y, SketchFrame.y_axis.z),
    )
    RadiusBase, RadiusX, RadiusY = (
        sum(map(Multiply, Radial, Value)) for Value in Basis
    )
    HeightBase, HeightX, HeightY = (
        sum(map(Multiply, AxisTuple, Value)) for Value in Basis
    )
    Corners = ReadCorners(ProfileLines)
    Meridian = tuple(
        (
            RadialLevel(RadiusBase, Point.x * RadiusX, Point.y * RadiusY),
            HeightBase + Point.x * HeightX + Point.y * HeightY,
        )
        for Point in Corners
    )
    Magnitudes = (
        *Offset,
        *(Value for Point in Corners for Value in (Point.x, Point.y)),
        *(Value for Coordinates in Meridian for Value in Coordinates),
    )
    Roundoff = 8.0 * FloatUlp(max(map(abs, Magnitudes)))
    return CleanMeridian(Meridian, Roundoff), SpaceVector(*Radial)
