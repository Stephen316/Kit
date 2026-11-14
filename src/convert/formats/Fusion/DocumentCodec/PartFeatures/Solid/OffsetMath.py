from typing import TypeAlias
from math import atan2 as ArcTangent, hypot as Hypotenuse, sqrt as SquareRoot

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    KFullTurn,
    SpanFinish,
    SpanHeading,
)

KPoint: TypeAlias = tuple[float, float]
KLine: TypeAlias = tuple[KPoint, KPoint]
KCircle: TypeAlias = tuple[KPoint, float]


def OffsetCircle(Value: KPlaneSpan, AmountCm: float) -> KCircle | None:
    if isinstance(Value, LineSpan):
        return None
    Radius = (
        Value.RadiusCm - AmountCm if Value.SweepAngle > 0 else Value.RadiusCm + AmountCm
    )
    if Radius <= 1e-9:
        raise ValueError("Fusion part offset consumes a profile arc")
    return Value.CenterCm, Radius


def TangentLine(Corner: KPoint, Heading: KPoint, AmountCm: float) -> KLine:
    return (
        (Corner[0] - Heading[1] * AmountCm, Corner[1] + Heading[0] * AmountCm),
        Heading,
    )


def LineCross(First: KLine, Second: KLine) -> list[KPoint]:
    (StartX, StartY), (HeadX, HeadY) = First
    (OtherX, OtherY), (TurnX, TurnY) = Second
    Cross = HeadX * TurnY - HeadY * TurnX
    if abs(Cross) < 1e-12:
        return []
    Along = ((OtherX - StartX) * TurnY - (OtherY - StartY) * TurnX) / Cross
    return [(StartX + HeadX * Along, StartY + HeadY * Along)]


def CircleLine(Circle: KCircle, Straight: KLine) -> list[KPoint]:
    (CenterX, CenterY), Radius = Circle
    (StartX, StartY), (HeadX, HeadY) = Straight
    DeltaX, DeltaY = StartX - CenterX, StartY - CenterY
    Middle = DeltaX * HeadX + DeltaY * HeadY
    Square = Middle * Middle - (DeltaX * DeltaX + DeltaY * DeltaY - Radius * Radius)
    if Square < -1e-12:
        return []
    Spread = SquareRoot(max(Square, 0.0))
    return [
        (StartX + HeadX * Along, StartY + HeadY * Along)
        for Along in (-Middle - Spread, -Middle + Spread)
    ]


def CircleCross(First: KCircle, Second: KCircle) -> list[KPoint]:
    (FirstX, FirstY), FirstRadius = First
    (OtherX, OtherY), OtherRadius = Second
    Apart = Hypotenuse(OtherX - FirstX, OtherY - FirstY)
    if Apart < 1e-12 or Apart > FirstRadius + OtherRadius + 1e-12:
        return []
    Along = (Apart * Apart + FirstRadius * FirstRadius - OtherRadius * OtherRadius) / (
        2 * Apart
    )
    Height = SquareRoot(max(FirstRadius * FirstRadius - Along * Along, 0.0))
    UnitX, UnitY = (OtherX - FirstX) / Apart, (OtherY - FirstY) / Apart
    BaseX, BaseY = FirstX + UnitX * Along, FirstY + UnitY * Along
    return [
        (BaseX - UnitY * Height, BaseY + UnitX * Height),
        (BaseX + UnitY * Height, BaseY - UnitX * Height),
    ]


def MixedCross(
    FirstArc: KCircle | None, OtherArc: KCircle | None, Lines: tuple[KLine, KLine]
) -> list[KPoint]:
    if FirstArc is not None and OtherArc is not None:
        return CircleCross(FirstArc, OtherArc)
    if FirstArc is not None:
        return CircleLine(FirstArc, Lines[1])
    if OtherArc is not None:
        return CircleLine(OtherArc, Lines[0])
    return LineCross(*Lines)


def OffsetJoint(Before: KPlaneSpan, After: KPlaneSpan, AmountCm: float) -> KPoint:
    Corner = SpanFinish(Before)
    Inward = SpanHeading(Before, True)
    Outward = SpanHeading(After, False)
    Naive = TangentLine(Corner, Inward, AmountCm)[0]
    Cross = Inward[0] * Outward[1] - Inward[1] * Outward[0]
    if abs(Cross) < 1e-9 and Inward[0] * Outward[0] + Inward[1] * Outward[1] > 0:
        return Naive
    Lines = (
        TangentLine(Corner, Inward, AmountCm),
        TangentLine(Corner, Outward, AmountCm),
    )
    Points = MixedCross(
        OffsetCircle(Before, AmountCm), OffsetCircle(After, AmountCm), Lines
    )
    if not Points:
        raise ValueError("Fusion part offset curves do not meet")
    return min(
        Points,
        key=lambda Point: Hypotenuse(Point[0] - Naive[0], Point[1] - Naive[1]),
    )


def ArcRange(
    Center: KPoint, Start: KPoint, Finish: KPoint, Sweep: float
) -> tuple[float, float]:
    Begin = ArcTangent(Start[1] - Center[1], Start[0] - Center[0])
    Final = ArcTangent(Finish[1] - Center[1], Finish[0] - Center[0])
    Delta = Final - Begin
    while Sweep > 0 and Delta <= 1e-12:
        Delta += KFullTurn
    while Sweep < 0 and Delta >= -1e-12:
        Delta -= KFullTurn
    return Begin, Delta
