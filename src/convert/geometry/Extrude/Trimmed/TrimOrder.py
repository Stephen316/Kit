# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import dist as Distance, ulp as UnitPlace

from convert.geometry.Extrude.Trimmed.TrimOperand import KTrimUse, TrimOperand
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.VectorPlane import PlaneVector

# joins need a small physical allowance for independently evaluated native endpoints
KJoinFloor = 1e-8


# endpoint tolerances scale only when local floating precision cannot resolve the floor
def JoinTolerance(Parts: tuple[TrimOperand, ...]) -> float:
    Scale = max(
        max(abs(Point.x), abs(Point.y))
        for PartValue in Parts
        for Point in (PartValue.Start, PartValue.Finish)
    )
    for PartValue in Parts:
        Geometry = PartValue.Geometry
        if isinstance(Geometry, ArcGeometry):
            Scale = max(
                Scale, abs(Geometry.center.x), abs(Geometry.center.y), Geometry.radius
            )
    return max(KJoinFloor, 8.0 * UnitPlace(Scale))


# mutual unique endpoint matches prove degree two without transitive snapping
def MatchTrimEnds(Points: tuple[PlaneVector, ...], Tolerance: float) -> tuple[int, ...]:
    Positions = tuple((Point.x, Point.y) for Point in Points)
    Matches = []
    for Index, Position in enumerate(Positions):
        Nearby = tuple(
            Other
            for Other, Candidate in enumerate(Positions)
            if Other != Index and Distance(Position, Candidate) <= Tolerance
        )
        if len(Nearby) != 1 or Nearby[0] // 2 == Index // 2:
            raise ValueError("Extrude trim endpoints are open, collapsed or branch")
        Matches.append(Nearby[0])
    return tuple(Matches)


# following each reciprocal join preserves the boundary without trusting source order
def WalkTrimRing(
    Parts: tuple[TrimOperand, ...],
    Points: tuple[PlaneVector, ...],
    Matches: tuple[int, ...],
) -> tuple[tuple[PlaneVector, ...], tuple[KTrimUse, ...]]:
    Ordered = []
    RingUses = []
    Visited = set()
    Cursor = 0
    while Cursor // 2 not in Visited:
        Index = Cursor // 2
        Visited.add(Index)
        Ordered.append(Points[min(Cursor, Matches[Cursor])])
        RingUses.append((Parts[Index], Cursor % 2 != 0))
        Cursor = Matches[Cursor ^ 1]
    if Cursor != 0 or len(Visited) != len(Parts):
        raise ValueError("Extrude trim boundary contains disconnected cycles")
    return tuple(Ordered), tuple(RingUses)
