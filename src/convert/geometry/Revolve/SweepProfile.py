# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import fsum as SumFinite
from math import hypot as Hypot
from math import isfinite as IsFinite


# the swept shell requires one convex positive radius meridian without repeated vertices
def MeridianSense(
    Meridian: tuple[tuple[float, float], ...],
    *,
    Strict: bool = False,
    AllowAxis: bool = False,
) -> int:
    if len(Meridian) < 3 or len(set(Meridian)) != len(Meridian):
        raise ValueError("revolution meridian requires distinct polygon vertices")
    if any(
        Radius < 0.0
        or (not AllowAxis and Radius == 0.0)
        or not IsFinite(Radius)
        or not IsFinite(Height)
        for Radius, Height in Meridian
    ):
        raise ValueError(
            "revolution meridian requires finite nonnegative radii and finite heights"
            if AllowAxis
            else "revolution meridian requires finite positive radii and finite heights"
        )
    AxisCorners = tuple(
        Index for Index, (Radius, _) in enumerate(Meridian) if Radius == 0.0
    )
    if AxisCorners and not (
        len(AxisCorners) == 2
        and AxisCorners[1] - AxisCorners[0] in (1, len(Meridian) - 1)
    ):
        raise ValueError(
            "full revolution axis contact requires one polygon side on the axis"
        )
    Winding = 0
    for Index, (Radius, Height) in enumerate(Meridian):
        EndRadius, EndHeight = Meridian[(Index + 1) % len(Meridian)]
        for PointIndex, (PointRadius, PointHeight) in enumerate(Meridian):
            if PointIndex in (Index, (Index + 1) % len(Meridian)):
                continue
            Side = (EndRadius - Radius) * (PointHeight - Height) - (
                EndHeight - Height
            ) * (PointRadius - Radius)
            if not IsFinite(Side):
                raise ValueError("revolution meridian exceeds finite geometry")
            if Strict and Side == 0.0:
                raise ValueError("Revolve meridian must be strictly convex")
            if Side:
                Direction = 1 if Side > 0.0 else -1
                if Winding and Direction != Winding:
                    raise ValueError(
                        "Revolve meridian must be strictly convex"
                        if Strict
                        else "revolution meridian must be a cyclic convex polygon"
                    )
                Winding = Direction
    if not Winding:
        raise ValueError("revolution meridian must have nonzero area")
    return Winding


# area and radial moment give the cap area and volume independently of angle
def ProfileMetrics(
    Meridian: tuple[tuple[float, float], ...], *, AllowAxis: bool = False
) -> tuple[float, float, float]:
    MeridianSense(Meridian, AllowAxis=AllowAxis)
    FirstRadius, FirstHeight = Meridian[0]
    Areas: list[float] = []
    Moments: list[float] = []
    for (Radius, Height), (EndRadius, EndHeight) in zip(Meridian[1:], Meridian[2:]):
        TriangleArea = (
            abs(
                (Radius - FirstRadius) * (EndHeight - FirstHeight)
                - (Height - FirstHeight) * (EndRadius - FirstRadius)
            )
            * 0.5
        )
        Areas.append(TriangleArea)
        MeanRadius = (FirstRadius / 3.0 + Radius / 3.0) + EndRadius / 3.0
        Moments.append(TriangleArea * MeanRadius)
    SideMoment = SumFinite(
        Hypot(EndRadius - Radius, EndHeight - Height) * (Radius * 0.5 + EndRadius * 0.5)
        for (Radius, Height), (EndRadius, EndHeight) in zip(
            Meridian, Meridian[1:] + Meridian[:1]
        )
    )
    return SumFinite(Areas), SumFinite(Moments), SideMoment
