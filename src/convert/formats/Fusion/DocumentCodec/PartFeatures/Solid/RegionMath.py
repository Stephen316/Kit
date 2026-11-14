from math import (
    atan2 as ArcTangent,
    cos as Cosine,
    hypot as Hypotenuse,
    sin as SineOf,
    sqrt as SquareRoot,
)

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    KFullTurn,
    ArcPoint,
    SpanFinish,
    SpanStart,
)

KRayAngle = 0.3713906763541037
KTouchLimit = 1e-7
KSampleCount = 32


def IsOnArc(Value: ArcSpan, Angle: float) -> bool:
    if abs(abs(Value.SweepAngle) - KFullTurn) < 1e-12:
        return True
    Offset = (Angle - Value.StartAngle) * (1.0 if Value.SweepAngle > 0 else -1.0)
    return Offset % KFullTurn <= abs(Value.SweepAngle)


def SpanDistance(Value: KPlaneSpan, Point: tuple[float, float]) -> float:
    if isinstance(Value, ArcSpan):
        DeltaX, DeltaY = Point[0] - Value.CenterCm[0], Point[1] - Value.CenterCm[1]
        if IsOnArc(Value, ArcTangent(DeltaY, DeltaX)):
            return abs(Hypotenuse(DeltaX, DeltaY) - Value.RadiusCm)
        EndPoints = (SpanStart(Value), SpanFinish(Value))
        return min(
            Hypotenuse(Point[0] - EndPoint[0], Point[1] - EndPoint[1])
            for EndPoint in EndPoints
        )
    StartX, StartY = Value.StartCm
    DeltaX, DeltaY = Value.FinishCm[0] - StartX, Value.FinishCm[1] - StartY
    Length = DeltaX * DeltaX + DeltaY * DeltaY
    Ratio = ((Point[0] - StartX) * DeltaX + (Point[1] - StartY) * DeltaY) / Length
    Ratio = min(1.0, max(0.0, Ratio))
    return Hypotenuse(
        Point[0] - StartX - Ratio * DeltaX, Point[1] - StartY - Ratio * DeltaY
    )


def RayCrossings(Value: KPlaneSpan, Point: tuple[float, float]) -> int:
    RayCos, RaySin = Cosine(KRayAngle), SineOf(KRayAngle)
    if isinstance(Value, LineSpan):
        StartX, StartY = Value.StartCm
        DeltaX, DeltaY = Value.FinishCm[0] - StartX, Value.FinishCm[1] - StartY
        Denominator = RayCos * DeltaY - RaySin * DeltaX
        if abs(Denominator) < 1e-15:
            return 0
        OffsetX, OffsetY = StartX - Point[0], StartY - Point[1]
        Along = (OffsetX * DeltaY - OffsetY * DeltaX) / Denominator
        Ratio = (OffsetX * RaySin - OffsetY * RayCos) / Denominator
        return int(Along > 0 and 0.0 <= Ratio < 1.0)
    OffsetX, OffsetY = Point[0] - Value.CenterCm[0], Point[1] - Value.CenterCm[1]
    Middle = OffsetX * RayCos + OffsetY * RaySin
    Spread = Middle * Middle - (OffsetX**2 + OffsetY**2 - Value.RadiusCm**2)
    if Spread <= 0:
        return 0
    Count = 0
    for Along in (-Middle - SquareRoot(Spread), -Middle + SquareRoot(Spread)):
        CrossX, CrossY = OffsetX + Along * RayCos, OffsetY + Along * RaySin
        Count += int(Along > 0 and IsOnArc(Value, ArcTangent(CrossY, CrossX)))
    return Count


def RegionSide(Loops: tuple[KPlaneLoop, ...], Point: tuple[float, float]) -> int:
    Spans = [Value for LoopValue in Loops for Value in LoopValue]
    if any(SpanDistance(Value, Point) < KTouchLimit for Value in Spans):
        return 0
    return 1 if sum(RayCrossings(Value, Point) for Value in Spans) % 2 else -1


def LoopSamples(LoopValue: KPlaneLoop) -> list[tuple[float, float]]:
    Points: list[tuple[float, float]] = []
    for Value in LoopValue:
        for Index in range(KSampleCount):
            Ratio = (Index + 0.5) / KSampleCount
            if isinstance(Value, ArcSpan):
                Points.append(
                    ArcPoint(Value, Value.StartAngle + Value.SweepAngle * Ratio)
                )
                continue
            Points.append(
                (
                    Value.StartCm[0] + (Value.FinishCm[0] - Value.StartCm[0]) * Ratio,
                    Value.StartCm[1] + (Value.FinishCm[1] - Value.StartCm[1]) * Ratio,
                )
            )
    return Points


def LoopPlace(LoopValue: KPlaneLoop, Loops: tuple[KPlaneLoop, ...]) -> int:
    Sides = {RegionSide(Loops, Point) for Point in LoopSamples(LoopValue)}
    if len(Sides) != 1 or 0 in Sides:
        raise ValueError("Fusion part profile boundaries overlap partially")
    return Sides.pop()
