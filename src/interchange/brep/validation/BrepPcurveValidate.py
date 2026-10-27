# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isfinite as IsFiniteNum

from interchange.brep.topology.BrepMath import (
    IsFinitePlane,
    IsNonzeroPlane,
    IsValidSpline,
)
from interchange.brep.curves.BrepPcurves import (
    BrepPcurve,
    CirclePcurve,
    LinePcurve,
    NativePcurve,
    NurbsPcurve,
)


# parameter curve validation protects surface trimming from malformed data
def GetPcurveErrors(CurveValue: BrepPcurve) -> tuple[str, ...]:
    IsValid = False
    if isinstance(CurveValue, LinePcurve):
        IsValid = IsFinitePlane(CurveValue.Origin) and IsNonzeroPlane(
            CurveValue.Direction
        )
    elif isinstance(CurveValue, CirclePcurve):
        IsValid = (
            IsFinitePlane(CurveValue.Center)
            and IsFiniteNum(CurveValue.Radius)
            and CurveValue.Radius > 0.0
        )
    elif isinstance(CurveValue, NurbsPcurve):
        IsValid = all(
            IsFinitePlane(PointValue) for PointValue in CurveValue.ControlPoints
        ) and IsValidSpline(
            CurveValue.Degree,
            len(CurveValue.ControlPoints),
            CurveValue.KnotValues,
            CurveValue.Multiplicities,
            CurveValue.Weights,
            CurveValue.IsPeriodic,
        )
    elif isinstance(CurveValue, NativePcurve):
        IsValid = bool(CurveValue.FormatId and CurveValue.EntityType)
    return () if IsValid else (f"B-rep pcurve {CurveValue.EntityId} is invalid",)
