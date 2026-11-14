from math import atan2 as ArcTangent

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.OffsetMath import KPoint
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    KFullTurn,
    IsFullCircle,
    SpanLength,
)

KSplitLimit = 1e-9


def SpanParam(Value: KPlaneSpan, Point: KPoint) -> float:
    if isinstance(Value, LineSpan):
        DeltaX = Value.FinishCm[0] - Value.StartCm[0]
        DeltaY = Value.FinishCm[1] - Value.StartCm[1]
        OffsetX, OffsetY = Point[0] - Value.StartCm[0], Point[1] - Value.StartCm[1]
        return (OffsetX * DeltaX + OffsetY * DeltaY) / SpanLength(Value)
    Angle = ArcTangent(Point[1] - Value.CenterCm[1], Point[0] - Value.CenterCm[0])
    Sense = 1.0 if Value.SweepAngle > 0 else -1.0
    return ((Angle - Value.StartAngle) * Sense % KFullTurn) * Value.RadiusCm


def CutParams(Value: KPlaneSpan, Points: list[KPoint]) -> list[float]:
    Length = SpanLength(Value)
    Params: list[float] = []
    for Point in Points:
        Param = SpanParam(Value, Point)
        if IsFullCircle(Value) and Param > Length - KSplitLimit:
            Param = 0.0
        IsInterior = KSplitLimit < Param < Length - KSplitLimit
        if (IsInterior or IsFullCircle(Value)) and all(
            abs(Param - Known) > KSplitLimit for Known in Params
        ):
            Params.append(Param)
    return sorted(Params)


def ArcPieces(Value: ArcSpan, Params: list[float]) -> list[KPlaneSpan]:
    Sense = 1.0 if Value.SweepAngle > 0 else -1.0
    Bounds = [0.0, *Params, SpanLength(Value)]
    if IsFullCircle(Value):
        Bounds = [*Params, Params[0] + SpanLength(Value)]
    return [
        ArcSpan(
            Value.CenterCm,
            Value.RadiusCm,
            Value.StartAngle + Sense * Lower / Value.RadiusCm,
            Sense * (Upper - Lower) / Value.RadiusCm,
            Value.Label,
        )
        for Lower, Upper in zip(Bounds, Bounds[1:])
    ]


def SplitSpan(Value: KPlaneSpan, Points: list[KPoint]) -> list[KPlaneSpan]:
    Params = CutParams(Value, Points)
    if not Params or (IsFullCircle(Value) and len(Params) == 1 and Params[0] == 0.0):
        return [Value]
    if isinstance(Value, ArcSpan):
        return ArcPieces(Value, Params)
    Length = SpanLength(Value)
    DeltaX = Value.FinishCm[0] - Value.StartCm[0]
    DeltaY = Value.FinishCm[1] - Value.StartCm[1]
    Corners = [Value.StartCm]
    for Param in Params:
        Ratio = Param / Length
        Corners.append(
            (Value.StartCm[0] + DeltaX * Ratio, Value.StartCm[1] + DeltaY * Ratio)
        )
    Corners.append(Value.FinishCm)
    return [
        LineSpan(Start, Finish, Value.Label)
        for Start, Finish in zip(Corners, Corners[1:])
    ]
