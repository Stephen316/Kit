# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isfinite as IsFinite
from math import tau as FullTurn

from convert.geometry.Revolve.SweepBounds import GetSweepBounds
from convert.geometry.Revolve.SweepInput import CheckSweepFrame
from convert.geometry.Revolve.SweepProfile import ProfileMetrics
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.VectorSpace import SpaceVector


# exact swept measures share the directed frame used by the resulting topology
def MeasureSweep(
    Meridian: tuple[tuple[float, float], ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
    StartRadians: float,
    EndRadians: float,
) -> tuple[float, float, BoundingBox]:
    """Measure a partial sweep of ordered radius and axial height pairs in millimetres."""
    Interval = EndRadians - StartRadians
    if not 0.0 < Interval < FullTurn:
        raise ValueError("revolution sweep requires a finite increasing partial turn")
    return MeasureInterval(
        Meridian, AxisOrigin, AxisDirection, Radial, StartRadians, EndRadians
    )


# a complete revolution has neither angular cap area nor an angular start plane
def MeasureFullTurn(
    Meridian: tuple[tuple[float, float], ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
) -> tuple[float, float, BoundingBox]:
    return MeasureInterval(Meridian, AxisOrigin, AxisDirection, Radial, 0.0, FullTurn)


# analytic volume area and extrema apply to both complete and bounded intervals
def MeasureInterval(
    Meridian: tuple[tuple[float, float], ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
    Radial: SpaceVector,
    StartRadians: float,
    EndRadians: float,
) -> tuple[float, float, BoundingBox]:
    CheckSweepFrame(AxisOrigin, AxisDirection, Radial)
    Interval = EndRadians - StartRadians
    if not 0.0 < Interval <= FullTurn:
        raise ValueError("revolution measure requires a finite increasing interval")
    IsFull = Interval == FullTurn
    try:
        CapArea, Moment, SideMoment = ProfileMetrics(Meridian, AllowAxis=True)
    except OverflowError as ErrorInfo:
        raise ValueError("revolution measures exceed finite geometry") from ErrorInfo
    Volume = Interval * Moment
    Surface = Interval * SideMoment + (0.0 if IsFull else 2.0 * CapArea)
    Bounds = GetSweepBounds(
        Meridian, AxisOrigin, AxisDirection, Radial, StartRadians, EndRadians
    )
    if not (
        0.0 < Volume
        and 0.0 < Surface
        and all(map(IsFinite, (Volume, Surface)))
        and all(
            IsFinite(Value)
            for Corner in (Bounds.minimum, Bounds.maximum)
            for Value in (Corner.x, Corner.y, Corner.z)
        )
    ):
        raise ValueError("revolution measures exceed finite geometry")
    return Volume, Surface, Bounds
