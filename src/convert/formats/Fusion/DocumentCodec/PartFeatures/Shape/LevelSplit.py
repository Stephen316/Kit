from math import hypot as Hypotenuse

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import SlabRoof
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    SpanFinish,
    SpanStart,
)

KPoint = tuple[float, float]
KPointTable = dict[KPoint, KPoint]
KSplitLimit = 1e-9


def PointKey(Point: KPoint) -> KPoint:
    return (round(Point[0], 9) + 0.0, round(Point[1], 9) + 0.0)


def LoopPoints(Loops: tuple[KPlaneLoop, ...]) -> tuple[KPoint, ...]:
    return tuple(
        Point
        for LoopValue in Loops
        for SpanValue in LoopValue
        for Point in (SpanStart(SpanValue), SpanFinish(SpanValue))
    )


def PointTable(Slabs: tuple[PrismSlab, ...]) -> KPointTable:
    Table: KPointTable = {}
    Loops = [
        LoopValue
        for SlabValue in Slabs
        for LoopValue in SlabValue.Loops + SlabValue.RoofLoops
    ]
    for Point in (SpanFinish(Value) for LoopValue in Loops for Value in LoopValue):
        _ = Table.setdefault(PointKey(Point), Point)
    for Point in (SpanStart(Value) for LoopValue in Loops for Value in LoopValue):
        _ = Table.setdefault(PointKey(Point), Point)
    return Table


def LevelPoints(Slabs: tuple[PrismSlab, ...]) -> dict[float, tuple[KPoint, ...]]:
    Points: dict[float, tuple[KPoint, ...]] = {}
    for SlabValue in Slabs:
        Lower, Upper = SlabValue.LowerCm, SlabValue.UpperCm
        Points[Lower] = Points.get(Lower, ()) + LoopPoints(SlabValue.Loops)
        Points[Upper] = Points.get(Upper, ()) + LoopPoints(SlabRoof(SlabValue))
    return Points


def LineRatio(SpanValue: LineSpan, Point: KPoint) -> float | None:
    Start, Finish = SpanValue.StartCm, SpanValue.FinishCm
    DeltaX, DeltaY = Finish[0] - Start[0], Finish[1] - Start[1]
    OffsetX, OffsetY = Point[0] - Start[0], Point[1] - Start[1]
    Length = Hypotenuse(DeltaX, DeltaY)
    if abs(OffsetX * DeltaY - OffsetY * DeltaX) > KSplitLimit * Length:
        return None
    return (OffsetX * DeltaX + OffsetY * DeltaY) / (Length * Length)


def SplitSpan(
    SpanValue: KPlaneSpan, Points: tuple[KPoint, ...], Table: KPointTable
) -> tuple[KPlaneSpan, ...]:
    if not isinstance(SpanValue, LineSpan):
        return (SpanValue,)
    Inner: dict[float, KPoint] = {}
    for Point in Points:
        Ratio = LineRatio(SpanValue, Point)
        if Ratio is not None and KSplitLimit < Ratio < 1.0 - KSplitLimit:
            _ = Inner.setdefault(round(Ratio, 9), Point)
    if not Inner:
        return (SpanValue,)
    Corners = [
        Table.get(PointKey(Point), Point)
        for Point in (
            SpanValue.StartCm,
            *(Inner[KeyValue] for KeyValue in sorted(Inner)),
            SpanValue.FinishCm,
        )
    ]
    return tuple(
        LineSpan(Former, Latter, SpanValue.Label)
        for Former, Latter in zip(Corners, Corners[1:])
    )
