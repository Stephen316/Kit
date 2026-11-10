# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import acos as ArcCos, atan2 as ArcTan, hypot as Hypot, isfinite as IsFinite
from math import tau as FullTurn

from convert.formats.Fusion.Profiles.Trimmed.TrimSources import (
    KTrimDistance,
    KTrimParameter,
)
from interchange.geometry.models.GeometryCurves import CircleGeometry


# proper native circle intersections establish cuts before selector ordinals are applied
def FindCircleCuts(
    Source: CircleGeometry, Others: tuple[CircleGeometry, ...]
) -> tuple[float, ...]:
    Radius = Source.radius
    CutValues: list[float] = []
    for Other in Others:
        DeltaX = Other.center.x - Source.center.x
        DeltaY = Other.center.y - Source.center.y
        Separation = Hypot(DeltaX, DeltaY)
        OtherRadius = Other.radius
        if not IsFinite(Separation) or Separation <= KTrimDistance:
            raise ValueError("Unsupported concentric Fusion trimmed circles")
        if Separation > Radius + OtherRadius + KTrimDistance:
            continue
        if not (
            abs(Radius - OtherRadius) + KTrimDistance
            < Separation
            < Radius + OtherRadius - KTrimDistance
        ):
            raise ValueError("Unsupported tangent or contained Fusion trimmed circles")
        Scale = max(Radius, OtherRadius, Separation)
        First, Second, Distance = (
            Radius / Scale,
            OtherRadius / Scale,
            Separation / Scale,
        )
        Denominator = 2.0 * First * Distance
        if Denominator <= 0.0:
            raise ValueError("Invalid Fusion trimmed circle intersection scale")
        Cosine = (First * First + Distance * Distance - Second * Second) / Denominator
        if not -1.0 < Cosine < 1.0:
            raise ValueError("Unsupported Fusion trimmed circle intersection")
        Angle = ArcTan(DeltaY, DeltaX)
        Spread = ArcCos(Cosine)
        CutValues.extend(((Angle - Spread) % FullTurn, (Angle + Spread) % FullTurn))
    CutValues.sort()
    if (
        len(CutValues) not in (2, 4)
        or CutValues[0] <= KTrimParameter
        or FullTurn - CutValues[-1] <= KTrimParameter
        or any(
            Upper - Lower <= KTrimParameter
            for Lower, Upper in zip(CutValues, CutValues[1:])
        )
    ):
        raise ValueError("Unsupported Fusion circle cut count or coincident seam")
    return tuple(CutValues)
