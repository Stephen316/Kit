# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Derive bounded meridian intervals from native construction planes."""

from math import atan2, hypot, isfinite, pi
from operator import mul, sub
from typing import NamedTuple


# candidate provenance distinguishes source geometry from a later cache choice
class PlaneInterval(NamedTuple):
    StartAngle: float
    EndAngle: float
    FirstBranch: int
    SecondBranch: int


# through axis limits admit two radial branches that must stay explicit
def PlaneBranches(PlaneOrigin, PlaneNormal, AxisOrigin, Axis, Radial, Tangent):
    """Return both roots in the source frame, ordered within one positive turn."""
    if any(
        len(Vector) != 3 or not all(map(isfinite, Vector))
        for Vector in (PlaneOrigin, PlaneNormal, AxisOrigin, Axis, Radial, Tangent)
    ):
        raise ValueError("Revolve plane operands require finite three-vectors")
    Offset = tuple(map(sub, PlaneOrigin, AxisOrigin))
    AlongAxis, AlongRadial, AlongTangent, Distance = (
        sum(map(mul, Vector, PlaneNormal)) for Vector in (Axis, Radial, Tangent, Offset)
    )
    Tolerance = 1e-9
    if (
        abs(hypot(*PlaneNormal) - 1.0) > Tolerance
        or abs(AlongAxis) > Tolerance
        or abs(Distance) > Tolerance
        or abs(hypot(AlongRadial, AlongTangent) - 1.0) > Tolerance
    ):
        raise ValueError("Revolve target must be a unit plane through the axis")
    Branch = atan2(-AlongRadial, AlongTangent) % pi
    if min(Branch, pi - Branch) <= Tolerance:
        Branch = 0.0
    return Branch, Branch + pi


# explicit candidates let callers validate shape without assuming a sweep direction
def PlaneIntervals(FirstRoots, SecondRoots=None):
    """Enumerate both directions between source or target meridians."""
    Starts = (0.0,) if SecondRoots is None else FirstRoots
    Ends = FirstRoots if SecondRoots is None else SecondRoots
    Intervals = []
    for FirstIndex, Start in enumerate(Starts):
        for SecondIndex, End in enumerate(Ends):
            Sweep = (End - Start) % (2.0 * pi)
            if min(Sweep, 2.0 * pi - Sweep) <= 1e-9:
                continue
            Intervals.extend(
                (
                    PlaneInterval(Start, Start + Sweep, FirstIndex, SecondIndex),
                    PlaneInterval(
                        Start, Start + Sweep - 2.0 * pi, FirstIndex, SecondIndex
                    ),
                )
            )
    if not Intervals:
        raise ValueError("Revolve target meridians yield no bounded interval")
    return tuple(Intervals)
