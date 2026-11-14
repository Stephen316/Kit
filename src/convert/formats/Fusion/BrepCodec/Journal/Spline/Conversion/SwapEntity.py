from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    SplineCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridResult import (
    GridResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.JumpCurve import (
    JumpCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

KMatchSlack = 1e-9


def IsNear(
    LeftPoints: tuple[tuple[float, ...], ...],
    RightPoints: tuple[tuple[float, ...], ...],
) -> bool:
    if len(LeftPoints) != len(RightPoints):
        return False
    Pairs = [
        (ValueLeft, ValueRight)
        for PointLeft, PointRight in zip(LeftPoints, RightPoints)
        for ValueLeft, ValueRight in zip(PointLeft, PointRight, strict=True)
    ]
    return all(
        abs(ValueLeft - ValueRight) <= KMatchSlack for ValueLeft, ValueRight in Pairs
    )


def SwapSurface(
    Value: SplineNode, Prior: GridResult, Result: GridResult, Surface: TsplineSurface
) -> SplineNode:
    if not isinstance(Value.Surface, TsplineSurf):
        return Value
    Cache = Value.Surface.Cache
    Knots = (Prior.Surface.KnotsU, Prior.Surface.KnotsV)
    if (Cache.KnotsU, Cache.KnotsV) != Knots or not IsNear(
        Cache.Points, Prior.Surface.Points
    ):
        raise ValueError("Fusion grid cage swap found a stale converted surface")
    if Value.Surface.Jumps != Prior.SurfaceJumps:
        raise ValueError("Fusion grid cage swap found stale surface discontinuities")
    Subtrans = Value.Surface.Subtrans
    if isinstance(Subtrans, SubtransNode):
        if Subtrans.Regions != (Prior.Patches,):
            raise ValueError("Fusion grid cage swap found another patch program")
        Subtrans = SubtransNode(Surface, (Result.Patches,))
    Changed = ReplaceValue(
        Value.Surface,
        Cache=Result.Surface,
        Jumps=Result.SurfaceJumps,
        Subtrans=Subtrans,
    )
    return ReplaceValue(Value, Surface=Changed)


def SwapCurve(
    Value: IntcurveNode, Prior: GridResult, Result: GridResult
) -> IntcurveNode:
    Stored = SplineCurve(Value.Curve)
    for Index, Bound in enumerate(Prior.Bounds):
        Shape = (Bound.Knots, Bound.Multiplicity, Bound.Weights)
        if Shape == (Stored.Knots, Stored.Multiplicity, Stored.Weights) and IsNear(
            Bound.Poles, Stored.Poles
        ):
            if JumpCurve(Stored, Prior.BoundJumps[Index]) != Value.Curve:
                raise ValueError("Fusion grid cage swap found another curve form")
            Curve = JumpCurve(Result.Bounds[Index], Result.BoundJumps[Index])
            return ReplaceValue(Value, Curve=Curve)
    raise ValueError("Fusion grid cage swap found a stale boundary curve")


def SwapPoint(Value: PointNode, Prior: GridResult, Result: GridResult) -> PointNode:
    for Index, Corner in enumerate(Prior.Corners):
        if IsNear((Corner,), (Value.PositionCm,)):
            return ReplaceValue(Value, PositionCm=Result.Corners[Index])
    raise ValueError("Fusion grid cage swap found a stale corner point")


def SwapEntity(
    Value: KJournalEntity,
    Prior: GridResult,
    Result: GridResult,
    Surface: TsplineSurface,
) -> KJournalEntity:
    if isinstance(Value, SplineNode):
        return SwapSurface(Value, Prior, Result, Surface)
    if isinstance(Value, IntcurveNode):
        return SwapCurve(Value, Prior, Result)
    if isinstance(Value, PointNode):
        return SwapPoint(Value, Prior, Result)
    return Value
