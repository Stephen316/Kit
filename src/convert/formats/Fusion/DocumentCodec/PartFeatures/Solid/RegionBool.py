from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LabelGroups import (
    MergeLabels,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import LoopArea
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PieceLink import (
    LinkPieces,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.RegionMath import (
    RegionSide,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SideProbe import SideProbe
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanCross import SpanCross
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    ArcPoint,
    ReverseSpan,
    SpanFinish,
    SpanStart,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SplitSpan import SplitSpan

KRegion = tuple[KPlaneLoop, ...]


def IsMember(
    Combine: str, First: KRegion, Second: KRegion, Point: tuple[float, float]
) -> bool:
    InFirst = RegionSide(First, Point) > 0
    InSecond = RegionSide(Second, Point) > 0
    if Combine == "join":
        return InFirst or InSecond
    if Combine == "cut":
        return InFirst and not InSecond
    if Combine == "intersect":
        return InFirst and InSecond
    raise ValueError("Unsupported Fusion part region operation")


def SplitLoops(Loops: KRegion, Others: KRegion) -> list[KPlaneSpan]:
    OtherSpans = [Value for LoopValue in Others for Value in LoopValue]
    Pieces: list[KPlaneSpan] = []
    for LoopValue in Loops:
        for Value in LoopValue:
            Points = [
                Point for Other in OtherSpans for Point in SpanCross(Value, Other)
            ]
            Pieces.extend(SplitSpan(Value, Points))
    return Pieces


def PieceKey(Value: KPlaneSpan) -> tuple[float, ...]:
    if isinstance(Value, ArcSpan):
        Middle = ArcPoint(Value, Value.StartAngle + Value.SweepAngle / 2.0)
    else:
        Start, Finish = SpanStart(Value), SpanFinish(Value)
        Middle = ((Start[0] + Finish[0]) / 2.0, (Start[1] + Finish[1]) / 2.0)
    Points = (SpanStart(Value), Middle, SpanFinish(Value))
    return tuple(round(Coordinate, 7) + 0.0 for Point in Points for Coordinate in Point)


def SelectPieces(First: KRegion, Second: KRegion, Combine: str) -> list[KPlaneSpan]:
    Chosen: dict[tuple[float, ...], KPlaneSpan] = {}
    for Piece in SplitLoops(First, Second) + SplitLoops(Second, First):
        LeftPoint, RightPoint = SideProbe(Piece)
        LeftIn = IsMember(Combine, First, Second, LeftPoint)
        if LeftIn == IsMember(Combine, First, Second, RightPoint):
            continue
        Oriented = Piece if LeftIn else ReverseSpan(Piece)
        KeyValue = PieceKey(Oriented)
        Known = Chosen.get(KeyValue)
        Chosen[KeyValue] = (
            Oriented
            if Known is None
            else ReplaceValue(Known, Label=MergeLabels(Known.Label, Oriented.Label))
        )
    return list(Chosen.values())


def RegionBool(First: KRegion, Second: KRegion, Combine: str) -> KRegion:
    Pieces = SelectPieces(First, Second, Combine)
    Loops = [CanonLoop(LoopValue) for LoopValue in LinkPieces(Pieces)]
    if any(abs(LoopArea(LoopValue)) < 1e-12 for LoopValue in Loops):
        raise ValueError("Fusion part region operation leaves a degenerate loop")
    Outer = [LoopValue for LoopValue in Loops if LoopArea(LoopValue) > 0]
    Holes = [LoopValue for LoopValue in Loops if LoopArea(LoopValue) < 0]
    return tuple(Outer + Holes)
