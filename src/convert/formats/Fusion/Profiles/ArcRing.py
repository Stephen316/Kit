# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import cos as Cos, dist as Dist, isclose as IsClose
from math import isfinite as IsFinite, pi as Pi, sin as Sin, ulp as Ulp

from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# profiles need the circular support evaluated at the original trim angles
def EvalArcPoint(ArcValue: ArcGeometry, Angle: float) -> PlaneVector:
    return PlaneVector(
        ArcValue.center.x + ArcValue.radius * Cos(Angle),
        ArcValue.center.y + ArcValue.radius * Sin(Angle),
    )


# a true diameter must close both ends of one whole semicircular arc
def CheckSemiRing(ArcValue: ArcGeometry, Diameter: LineGeometry) -> None:
    Angles = (ArcValue.start_angle, ArcValue.end_angle)
    Values = (ArcValue.center.x, ArcValue.center.y, ArcValue.radius, *Angles)
    if (
        not all(map(IsFinite, Values))
        or ArcValue.radius <= 0.0
        or not IsClose(Angles[1] - Angles[0], Pi, rel_tol=0.0, abs_tol=1e-10)
    ):
        raise ValueError("Fusion curved profile requires a semicircle")
    Start, Finish = (EvalArcPoint(ArcValue, Angle) for Angle in Angles)
    Ends = ((Diameter.start.x, Diameter.start.y), (Diameter.end.x, Diameter.end.y))
    ArcEnds = ((Start.x, Start.y), (Finish.x, Finish.y))
    Tolerance = max(1e-8, 8.0 * Ulp(max(map(abs, Values[:3]))))
    if (
        not all(IsFinite(Value) for Point in (*ArcEnds, *Ends) for Value in Point)
        or Dist(*Ends) <= Tolerance
        or not any(
            all(
                Dist(First, Second) <= Tolerance
                for First, Second in zip(ArcEnds, Order)
            )
            for Order in (Ends, Ends[::-1])
        )
    ):
        raise ValueError("Fusion semicircle diameter does not close the arc endpoints")
