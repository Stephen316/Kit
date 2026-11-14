from math import atan2 as ArcTangent, cos as Cosine, hypot as Hypotenuse, sin as SineOf

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan

KFullTurn = 6.283185307179586
KTolerance = 1e-9


def ArcPoint(Value: ArcSpan, Angle: float) -> tuple[float, float]:
    return (
        Value.CenterCm[0] + Value.RadiusCm * Cosine(Angle),
        Value.CenterCm[1] + Value.RadiusCm * SineOf(Angle),
    )


def SpanStart(Value: KPlaneSpan) -> tuple[float, float]:
    if isinstance(Value, LineSpan):
        return Value.StartCm
    return ArcPoint(Value, Value.StartAngle)


def SpanFinish(Value: KPlaneSpan) -> tuple[float, float]:
    if isinstance(Value, LineSpan):
        return Value.FinishCm
    return ArcPoint(Value, Value.StartAngle + Value.SweepAngle)


def IsFullCircle(Value: KPlaneSpan) -> bool:
    return isinstance(Value, ArcSpan) and abs(abs(Value.SweepAngle) - KFullTurn) < 1e-9


def SpanHeading(Value: KPlaneSpan, AtFinish: bool) -> tuple[float, float]:
    if isinstance(Value, LineSpan):
        DeltaX = Value.FinishCm[0] - Value.StartCm[0]
        DeltaY = Value.FinishCm[1] - Value.StartCm[1]
        Length = Hypotenuse(DeltaX, DeltaY)
        return (DeltaX / Length, DeltaY / Length)
    Angle = Value.StartAngle + (Value.SweepAngle if AtFinish else 0.0)
    Sense = 1.0 if Value.SweepAngle > 0 else -1.0
    return (-SineOf(Angle) * Sense, Cosine(Angle) * Sense)


def SpanLength(Value: KPlaneSpan) -> float:
    if isinstance(Value, LineSpan):
        return Hypotenuse(
            Value.FinishCm[0] - Value.StartCm[0], Value.FinishCm[1] - Value.StartCm[1]
        )
    return Value.RadiusCm * abs(Value.SweepAngle)


def ReverseSpan(Value: KPlaneSpan) -> KPlaneSpan:
    if isinstance(Value, LineSpan):
        return LineSpan(Value.FinishCm, Value.StartCm, Value.Label)
    return ArcSpan(
        Value.CenterCm,
        Value.RadiusCm,
        Value.StartAngle + Value.SweepAngle,
        -Value.SweepAngle,
        Value.Label,
    )


def PointAngle(Center: tuple[float, float], Point: tuple[float, float]) -> float:
    return ArcTangent(Point[1] - Center[1], Point[0] - Center[0])
