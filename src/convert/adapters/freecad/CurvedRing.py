# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isfinite as IsFinite

from convert.geometry.Extrude.Trimmed.TrimMeasures import MeasureTrim
from convert.geometry.Extrude.Trimmed.TrimOperand import ReadOperand
from convert.geometry.Extrude.Trimmed.TrimOrder import MatchTrimEnds
from convert.geometry.Extrude.Trimmed.TrimSimple import CheckTrimSimple
from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry


# native planar trimming needs proven simplicity and signed winding in the actual coedge order
def CurvedRingArea(
    Geometries: tuple[tuple[LineGeometry | ArcGeometry, bool], ...],
    Tolerance: float,
) -> float | None:
    if len(Geometries) < 2:
        return None
    try:
        if (
            type(Tolerance) not in (int, float)
            or not IsFinite(Tolerance)
            or Tolerance < 0.0
            or not any(isinstance(Geometry, ArcGeometry) for Geometry, _ in Geometries)
            or any(type(Reversed) is not bool for _, Reversed in Geometries)
        ):
            return None
        RingUses = tuple(
            (ReadOperand(Geometry), Reversed) for Geometry, Reversed in Geometries
        )
        Parts = tuple(Value for Value, _ in RingUses)
        Points = tuple(
            Point for Value in Parts for Point in (Value.Start, Value.Finish)
        )
        Matches = MatchTrimEnds(Points, Tolerance)
        Entries = tuple(
            2 * Index + int(Reversed) for Index, (_, Reversed) in enumerate(RingUses)
        )
        if any(
            Matches[Entry ^ 1] != Following
            for Entry, Following in zip(Entries, Entries[1:] + Entries[:1])
        ):
            return None
        CheckTrimSimple(Parts, Points, Matches, Tolerance)
        AreaValue, _ = MeasureTrim(
            tuple(Points[min(Entry, Matches[Entry])] for Entry in Entries), RingUses
        )
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None
    return AreaValue if abs(AreaValue) > Tolerance * Tolerance else None
