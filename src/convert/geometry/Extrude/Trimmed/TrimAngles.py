# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import atan2 as AngleOf, cos as Cosine, dist as Distance
from math import sin as SineValue, tau as FullTurn

from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# relative trigonometric phases avoid a modulo error when large native angles wrap
def AngleFrom(Angle: float, Origin: float) -> float:
    CosineAngle, SineAngle = Cosine(Angle), SineValue(Angle)
    CosineOrigin, SineOrigin = Cosine(Origin), SineValue(Origin)
    return (
        AngleOf(
            SineAngle * CosineOrigin - CosineAngle * SineOrigin,
            CosineAngle * CosineOrigin + SineAngle * SineOrigin,
        )
        % FullTurn
    )


# carrier intersections matter only inside each original bounded angular window
def IsOnTrimArc(ArcValue: ArcGeometry, Point: PlaneVector, Tolerance: float) -> bool:
    DeltaX, DeltaY = Point.x - ArcValue.center.x, Point.y - ArcValue.center.y
    if abs(Distance((DeltaX, DeltaY), (0.0, 0.0)) - ArcValue.radius) > Tolerance:
        return False
    Angle = AngleFrom(AngleOf(DeltaY, DeltaX), ArcValue.start_angle)
    AngularTol = Tolerance / ArcValue.radius
    return (
        Angle <= ArcValue.end_angle - ArcValue.start_angle + AngularTol
        or FullTurn - Angle <= AngularTol
    )


# disjoint trims may share a periodic carrier without duplicating the same boundary
def HasArcOverlap(First: ArcGeometry, Second: ArcGeometry, Tolerance: float) -> bool:
    Shift = AngleFrom(Second.start_angle, First.start_angle)
    FirstSpan = First.end_angle - First.start_angle
    SecondSpan = Second.end_angle - Second.start_angle
    return any(
        min(FirstSpan, Start + SecondSpan) - max(0.0, Start) > Tolerance / First.radius
        for Start in (Shift, Shift - FullTurn)
    )
