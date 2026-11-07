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


# fixed plane contrasts establish the forward sector for this source family
def SelectPlaneSpan(PlaneRoots):
    """Select the observed positive sweep in the sketch-normal-directed frame."""
    if len(PlaneRoots) == 1:
        ((Forward, _),) = PlaneRoots
        if Forward <= 1e-9:
            raise ValueError("Revolve target plane coincides with the sketch plane")
        return 0.0, Forward
    if len(PlaneRoots) != 2:
        raise ValueError("Revolve requires one or two target planes")
    Earlier, Later = sorted(PlaneRoots)
    if Earlier[0] <= 1e-9 or Later[0] - Earlier[0] <= 1e-9:
        raise ValueError("Revolve target planes coincide with the sketch or each other")
    return Later[0], Earlier[1]
