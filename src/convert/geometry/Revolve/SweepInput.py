# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose, isfinite as IsFinite, tau as Tau

from convert.geometry.Revolve.SweepVector import DotVector
from interchange.brep.topology.BrepMath import IsFiniteSpace
from interchange.geometry.models.VectorSpace import SpaceVector


# strict convexity gives a single outward sense to every lateral face
def OrientMeridian(
    Meridian: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    if len(Meridian) < 3 or not all(
        IsFinite(Radius) and IsFinite(Height) and Radius > 0.0
        for Radius, Height in Meridian
    ):
        raise ValueError("Revolve meridian requires at least three positive radii")
    Winding = 0
    for Index, (Radius, Height) in enumerate(Meridian):
        Following = (Index + 1) % len(Meridian)
        NextRadius, NextHeight = Meridian[Following]
        DeltaRadius = NextRadius - Radius
        DeltaHeight = NextHeight - Height
        for Offset, (OtherRadius, OtherHeight) in enumerate(Meridian):
            if Offset in (Index, Following):
                continue
            Cross = DeltaRadius * (OtherHeight - Height) - DeltaHeight * (
                OtherRadius - Radius
            )
            if not IsFinite(Cross) or Cross == 0.0:
                raise ValueError("Revolve meridian must be strictly convex")
            SignValue = 1 if Cross > 0.0 else -1
            if Winding and Winding != SignValue:
                raise ValueError("Revolve meridian must be strictly convex")
            Winding = SignValue
    return Meridian if Winding > 0 else Meridian[:1] + Meridian[:0:-1]


# finite orthonormal frames and open angular ranges avoid collapsed sweeps
def CheckSweepInput(
    BodyId: str,
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
    StartRadians: float,
    EndRadians: float,
) -> None:
    if not BodyId or not IsFiniteSpace(AxisOrigin):
        raise ValueError("Revolve body identity and finite axis origin are required")
    if (
        not IsClose(DotVector(AxisDirection, AxisDirection), 1.0, abs_tol=1e-9)
        or not IsClose(DotVector(Radial, Radial), 1.0, abs_tol=1e-9)
        or not IsClose(DotVector(AxisDirection, Radial), 0.0, abs_tol=1e-9)
    ):
        raise ValueError("Revolve axis and radial directions must be orthonormal")
    SpanValue = EndRadians - StartRadians
    if not 0.0 < SpanValue < Tau:
        raise ValueError("Revolve solid requires a positive partial turn")
