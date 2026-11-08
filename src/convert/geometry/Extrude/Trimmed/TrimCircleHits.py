# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot, sqrt as SquareRoot

from convert.geometry.Extrude.Polygon.RingPredicates import ToRingGrid
from convert.geometry.Extrude.Trimmed.TrimAngles import HasArcOverlap, IsOnTrimArc
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# circle intersection discriminants separate overlap tangency and disjoint carriers exactly
def GetArcArcHits(
    First: ArcGeometry, Second: ArcGeometry, Tolerance: float
) -> tuple[PlaneVector, ...]:
    (Center, Other, Radii), _ = ToRingGrid(
        (First.center, Second.center, PlaneVector(First.radius, Second.radius))
    )
    DeltaX, DeltaY = Other[0] - Center[0], Other[1] - Center[1]
    Separation = DeltaX**2 + DeltaY**2
    RadiusA, RadiusB = Radii
    if Separation == 0:
        if RadiusA == RadiusB and HasArcOverlap(First, Second, Tolerance):
            raise ValueError("Extrude trim has overlapping coincident circular arcs")
        return ()
    Exterior = (RadiusA + RadiusB) ** 2 - Separation
    Interior = Separation - (RadiusA - RadiusB) ** 2
    if Exterior < 0 or Interior < 0:
        return ()
    Along = (Separation + RadiusA**2 - RadiusB**2) / (2 * Separation)
    Spread = (
        SquareRoot(Exterior * Interior / (4 * Separation * RadiusA**2)) * First.radius
    )
    SpanX = Second.center.x - First.center.x
    SpanY = Second.center.y - First.center.y
    Length = Hypot(SpanX, SpanY)
    Points = (
        PlaneVector(
            First.center.x + Along * SpanX - Direction * Spread * (SpanY / Length),
            First.center.y + Along * SpanY + Direction * Spread * (SpanX / Length),
        )
        for Direction in (-1.0, 1.0)
    )
    return tuple(
        Point
        for Point in Points
        if IsOnTrimArc(First, Point, Tolerance)
        and IsOnTrimArc(Second, Point, Tolerance)
    )
