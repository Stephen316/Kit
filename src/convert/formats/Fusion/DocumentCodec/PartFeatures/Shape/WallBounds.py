from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelSplit import (
    KPoint,
    KPointTable,
    LineRatio,
    PointKey,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.RangeMath import (
    KRange,
    KRangeLimit,
    RangeMinus,
    SplitRanges,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.RiseEdge import RiseEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallPiece import WallPiece
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import SpanHeading

KSides = dict[KPoint, tuple[list[KRange], list[KRange]]]
KLevelMap = dict[float, tuple[KPoint, ...]]
KTrack = tuple[LineSpan, KPoint, tuple[float, float]]


def TrackParam(Track: KTrack, Point: KPoint) -> float:
    _, Origin, Heading = Track
    return (Point[0] - Origin[0]) * Heading[0] + (Point[1] - Origin[1]) * Heading[1]


def TrackRange(Track: KTrack, SpanValue: KPlaneSpan) -> KRange:
    if not isinstance(SpanValue, LineSpan):
        raise ValueError("Fusion part merged walls must be straight")
    return TrackParam(Track, SpanValue.StartCm), TrackParam(Track, SpanValue.FinishCm)


def TrackSpan(
    Track: KTrack, Members: list[WallPiece], Bounds: KRange, Exact: dict[float, KPoint]
) -> KPlaneSpan:
    for Member in Members:
        Lower, Upper = TrackRange(Track, Member.Span)
        if (
            abs(Lower - Bounds[0]) < KRangeLimit
            and abs(Upper - Bounds[1]) < KRangeLimit
        ):
            return Member.Span
    Start, Finish = Exact[round(Bounds[0], 9)], Exact[round(Bounds[1], 9)]
    return LineSpan(Start, Finish, Track[0].Label)


def TrackPoints(
    Track: KTrack, Members: list[WallPiece], Points: KLevelMap, Table: KPointTable
) -> dict[float, KPoint]:
    Exact: dict[float, KPoint] = {}
    Candidates = [
        Point
        for Member in Members
        for Point in (*TrackPoint(Member.Span), *Points.get(Member.LowerCm, ()))
    ] + [Point for Member in Members for Point in Points.get(Member.UpperCm, ())]
    for Point in Candidates:
        if LineRatio(Track[0], Point) is not None:
            _ = Exact.setdefault(
                round(TrackParam(Track, Point), 9), Table.get(PointKey(Point), Point)
            )
    return Exact


def TrackPoint(SpanValue: KPlaneSpan) -> tuple[KPoint, ...]:
    if not isinstance(SpanValue, LineSpan):
        return ()
    return SpanValue.StartCm, SpanValue.FinishCm


def LineLevels(
    Members: list[WallPiece], Points: KLevelMap, Table: KPointTable
) -> tuple[list[ShapeUse], list[ShapeUse]]:
    Leader = Members[0].Span
    if not isinstance(Leader, LineSpan):
        raise ValueError("Fusion part merged walls must be straight")
    Track = (Leader, Leader.StartCm, SpanHeading(Leader, False))
    Exact = TrackPoints(Track, Members, Points, Table)
    Bottoms: list[ShapeUse] = []
    TopUses: list[ShapeUse] = []
    Levels = sorted(
        {Value for Member in Members for Value in (Member.LowerCm, Member.UpperCm)}
    )
    for Level in Levels:
        CutValues = [
            TrackParam(Track, Point)
            for Point in Points.get(Level, ())
            if LineRatio(Leader, Point) is not None
        ]
        Rising = [Member for Member in Members if Member.LowerCm == Level]
        Falling = [Member for Member in Members if Member.UpperCm == Level]
        Below = [TrackRange(Track, Member.Span) for Member in Rising]
        Above = [TrackRange(Track, Member.Span) for Member in Falling]
        for Bounds in SplitRanges(RangeMinus(Below, Above), CutValues):
            SpanValue = TrackSpan(Track, Rising, Bounds, Exact)
            Bottoms.append(ShapeUse(LevelEdge(SpanValue, Level), True))
        for Bounds in reversed(SplitRanges(RangeMinus(Above, Below), CutValues)):
            SpanValue = TrackSpan(Track, Falling, Bounds, Exact)
            TopUses.append(ShapeUse(LevelEdge(SpanValue, Level), False))
    return Bottoms, TopUses


def GroupLevels(
    Members: list[WallPiece], Points: KLevelMap, Table: KPointTable
) -> tuple[list[ShapeUse], list[ShapeUse]]:
    Leader = Members[0].Span
    if isinstance(Leader, LineSpan):
        return LineLevels(Members, Points, Table)
    Lower = min(Member.LowerCm for Member in Members)
    Upper = max(Member.UpperCm for Member in Members)
    Bottom = ShapeUse(LevelEdge(Leader, Lower), True)
    return [Bottom], [ShapeUse(LevelEdge(Leader, Upper), False)]


def GroupSides(Members: list[WallPiece]) -> KSides:
    Starts: dict[KPoint, list[KRange]] = {}
    Finishes: dict[KPoint, list[KRange]] = {}
    for Member in Members:
        Height = (Member.LowerCm, Member.UpperCm)
        Starts.setdefault(PointKey(Member.Joints[0]), []).append(Height)
        Finishes.setdefault(PointKey(Member.Joints[1]), []).append(Height)
    Sides: KSides = {}
    for KeyValue in [*Starts, *(Value for Value in Finishes if Value not in Starts)]:
        Rising, Falling = Starts.get(KeyValue, []), Finishes.get(KeyValue, [])
        Sides[KeyValue] = (RangeMinus(Rising, Falling), RangeMinus(Falling, Rising))
    return Sides


def SideBreaks(Sides: list[KSides]) -> dict[KPoint, list[float]]:
    Breaks: dict[KPoint, list[float]] = {}
    for SideMap in Sides:
        for KeyValue, PairValue in SideMap.items():
            EndValues = [
                Value for Bounds in PairValue[0] + PairValue[1] for Value in Bounds
            ]
            Breaks.setdefault(KeyValue, []).extend(EndValues)
    return Breaks


def SideUses(
    Sides: KSides, Breaks: dict[KPoint, list[float]], Table: KPointTable
) -> tuple[list[ShapeUse], list[ShapeUse]]:
    Upward: list[ShapeUse] = []
    Downward: list[ShapeUse] = []
    for KeyValue, (Starting, Finishing) in Sides.items():
        Point = Table.get(KeyValue, KeyValue)
        CutValues = Breaks.get(KeyValue, [])
        for Lower, Upper in SplitRanges(Finishing, CutValues):
            Upward.append(ShapeUse(RiseEdge(Point, Lower, Upper), True))
        for Lower, Upper in reversed(SplitRanges(Starting, CutValues)):
            Downward.append(ShapeUse(RiseEdge(Point, Lower, Upper), False))
    return Upward, Downward
