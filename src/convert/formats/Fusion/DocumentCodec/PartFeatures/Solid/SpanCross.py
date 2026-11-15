from math import hypot as Hypotenuse

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.OffsetMath import (
    CircleCross,
    CircleLine,
    KPoint,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.RegionMath import (
    SpanDistance,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    SpanFinish,
    SpanStart,
)

# the meet limit tolerance prevents rounding noise from creating false geometric distinctions during reconstruction
KMeetLimit = 1e-9


# the on both decision must stay consistent so body topology remains consistent with its modeling operation
def IsOnBoth(First: KPlaneSpan, Second: KPlaneSpan, Point: KPoint) -> bool:
    return (
        SpanDistance(First, Point) < KMeetLimit
        and SpanDistance(Second, Point) < KMeetLimit
    )


# shared ends needs a shared interpretation so body topology remains consistent with its modeling operation
def SharedEnds(First: KPlaneSpan, Second: KPlaneSpan) -> list[KPoint]:
    Points = [SpanStart(First), SpanFinish(First), SpanStart(Second)]
    Points.append(SpanFinish(Second))
    return [Point for Point in Points if IsOnBoth(First, Second, Point)]


# the line meet contract needs a shared interpretation so body topology remains consistent with its modeling operation
def LineMeet(First: LineSpan, Second: LineSpan) -> list[KPoint]:
    (StartX, StartY), (FinishX, FinishY) = First.StartCm, First.FinishCm
    (OtherX, OtherY), (FarAlongX, FarAlongY) = Second.StartCm, Second.FinishCm
    AlongX, AlongY = FinishX - StartX, FinishY - StartY
    AcrossX, AcrossY = FarAlongX - OtherX, FarAlongY - OtherY
    Cross = AlongX * AcrossY - AlongY * AcrossX
    Scale = Hypotenuse(AlongX, AlongY) * Hypotenuse(AcrossX, AcrossY)
    if abs(Cross) <= 1e-12 * Scale:
        return SharedEnds(First, Second)
    Ratio = ((OtherX - StartX) * AcrossY - (OtherY - StartY) * AcrossX) / Cross
    Point = (StartX + AlongX * Ratio, StartY + AlongY * Ratio)
    return [Point] if IsOnBoth(First, Second, Point) else []


# the line heading contract needs a shared interpretation so body topology remains consistent with its modeling operation
def LineHeading(Value: LineSpan) -> tuple[KPoint, KPoint]:
    DeltaX = Value.FinishCm[0] - Value.StartCm[0]
    DeltaY = Value.FinishCm[1] - Value.StartCm[1]
    Length = Hypotenuse(DeltaX, DeltaY)
    return Value.StartCm, (DeltaX / Length, DeltaY / Length)


# the arc meet contract needs a shared interpretation so body topology remains consistent with its modeling operation
def ArcMeet(First: ArcSpan, Second: KPlaneSpan) -> list[KPoint]:
    Circle = (First.CenterCm, First.RadiusCm)
    if isinstance(Second, LineSpan):
        Points = CircleLine(Circle, LineHeading(Second))
    else:
        Apart = Hypotenuse(
            First.CenterCm[0] - Second.CenterCm[0],
            First.CenterCm[1] - Second.CenterCm[1],
        )
        if Apart < KMeetLimit and abs(First.RadiusCm - Second.RadiusCm) < KMeetLimit:
            return SharedEnds(First, Second)
        Points = CircleCross(Circle, (Second.CenterCm, Second.RadiusCm))
    return [Point for Point in Points if IsOnBoth(First, Second, Point)]


# the span cross contract needs a shared interpretation so body topology remains consistent with its modeling operation
def SpanCross(First: KPlaneSpan, Second: KPlaneSpan) -> list[KPoint]:
    if isinstance(First, ArcSpan):
        return ArcMeet(First, Second)
    if isinstance(Second, ArcSpan):
        return ArcMeet(Second, First)
    return LineMeet(First, Second)
