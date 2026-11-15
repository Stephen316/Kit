from math import atan2 as ArcTangent, cos as Cosine, hypot as Hypotenuse, sin as SineOf

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan

# full turn must remain consistent across callers so body topology remains consistent with its modeling operation
KFullTurn = 6.283185307179586

# the tolerance tolerance prevents rounding noise from creating false geometric distinctions during reconstruction
KTolerance = 1e-9


# the arc point contract needs a shared interpretation so body topology remains consistent with its modeling operation
def ArcPoint(Value: ArcSpan, Angle: float) -> tuple[float, float]:
    return (
        Value.CenterCm[0] + Value.RadiusCm * Cosine(Angle),
        Value.CenterCm[1] + Value.RadiusCm * SineOf(Angle),
    )


# the span start contract needs a shared interpretation so body topology remains consistent with its modeling operation
def SpanStart(Value: KPlaneSpan) -> tuple[float, float]:
    if isinstance(Value, LineSpan):
        return Value.StartCm
    return ArcPoint(Value, Value.StartAngle)


# the span finish contract needs a shared interpretation so body topology remains consistent with its modeling operation
def SpanFinish(Value: KPlaneSpan) -> tuple[float, float]:
    if isinstance(Value, LineSpan):
        return Value.FinishCm
    return ArcPoint(Value, Value.StartAngle + Value.SweepAngle)


# the full circle decision must stay consistent so body topology remains consistent with its modeling operation
def IsFullCircle(Value: KPlaneSpan) -> bool:
    return isinstance(Value, ArcSpan) and abs(abs(Value.SweepAngle) - KFullTurn) < 1e-9


# the span heading contract needs a shared interpretation so body topology remains consistent with its modeling operation
def SpanHeading(Value: KPlaneSpan, AtFinish: bool) -> tuple[float, float]:
    if isinstance(Value, LineSpan):
        DeltaX = Value.FinishCm[0] - Value.StartCm[0]
        DeltaY = Value.FinishCm[1] - Value.StartCm[1]
        Length = Hypotenuse(DeltaX, DeltaY)
        return (DeltaX / Length, DeltaY / Length)
    Angle = Value.StartAngle + (Value.SweepAngle if AtFinish else 0.0)
    Sense = 1.0 if Value.SweepAngle > 0 else -1.0
    return (-SineOf(Angle) * Sense, Cosine(Angle) * Sense)


# the span length contract needs a shared interpretation so body topology remains consistent with its modeling operation
def SpanLength(Value: KPlaneSpan) -> float:
    if isinstance(Value, LineSpan):
        return Hypotenuse(
            Value.FinishCm[0] - Value.StartCm[0], Value.FinishCm[1] - Value.StartCm[1]
        )
    return Value.RadiusCm * abs(Value.SweepAngle)


# the reverse span contract needs a shared interpretation so body topology remains consistent with its modeling operation
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


# the angle operation needs one geometric convention so body topology remains consistent with its modeling operation
def PointAngle(Center: tuple[float, float], Point: tuple[float, float]) -> float:
    return ArcTangent(Point[1] - Center[1], Point[0] - Center[0])
