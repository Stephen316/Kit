# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import fsum as SumFinite
from math import hypot as Hypot
from math import isclose as IsClose
from math import isfinite as IsFinite
from math import tau as FullTurn

from convert.geometry.Revolve.SweepBounds import GetSweepBounds
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
    Span = EndRadians - StartRadians
    if not 0.0 < Span < FullTurn:
        raise ValueError("revolution sweep requires a finite increasing partial turn")
    AxisValues = (AxisDirection.x, AxisDirection.y, AxisDirection.z)
    RadialValues = (Radial.x, Radial.y, Radial.z)
    OriginValues = (AxisOrigin.x, AxisOrigin.y, AxisOrigin.z)
    if not (
        all(map(IsFinite, OriginValues))
        and IsClose(Hypot(*AxisValues), 1.0, abs_tol=1e-9, rel_tol=0.0)
        and IsClose(Hypot(*RadialValues), 1.0, abs_tol=1e-9, rel_tol=0.0)
        and abs(
            SumFinite(Axis * Radius for Axis, Radius in zip(AxisValues, RadialValues))
        )
        <= 1e-9
    ):
        raise ValueError(
            "revolution sweep requires a finite orthonormal axis and radial"
        )
    try:
        Area, Moment, SideMoment = ProfileMetrics(Meridian)
    except OverflowError as ErrorInfo:
        raise ValueError("revolution measures exceed finite geometry") from ErrorInfo
    Volume = Span * Moment
    Surface = 2.0 * Area + Span * SideMoment
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
