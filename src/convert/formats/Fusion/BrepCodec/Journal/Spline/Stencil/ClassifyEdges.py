from collections.abc import Callable
from dataclasses import replace as ReplaceValue
from functools import partial as BindArgs
import math

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormFace,
    FormUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SplineFrame import (
    CurveFrame,
    SurfaceFrame,
)

KTangentTurn = math.radians(1.0)
KFlatTurn = 1e-12
KCreaseSamples = 8
KPeakSteps = 32
KRootSteps = 2100
KGoldenCut = (math.sqrt(5.0) - 1.0) / 2.0
KCreaseSide = tuple[NubsSurface, FormUse]
KCreaseTurn = Callable[[float], float]
KCreaseSpan = list[tuple[float, float]]
KCreasePiece = tuple[float, float, str]
KCreaseFault = "Fusion Form conversion may split or reclassify a crease edge"
KSeamSlack = 1e-9
KTurnRate = 0.01
KEndHalves = (8.0, 4.0, 2.0)
KEndReach = len(KEndHalves) + 1
KCreaseMark = float | None


def CrossValue(First: list[float], Second: list[float]) -> list[float]:
    return [
        First[1] * Second[2] - First[2] * Second[1],
        First[2] * Second[0] - First[0] * Second[2],
        First[0] * Second[1] - First[1] * Second[0],
    ]


def UnitValue(Vector: list[float]) -> list[float]:
    Length = math.sqrt(sum(Entry * Entry for Entry in Vector))
    if Length == 0.0:
        raise ValueError("Fusion Form crease check found a degenerate frame")
    return [Entry / Length for Entry in Vector]


def SideNormal(SideValue: KCreaseSide, Param: float) -> list[float]:
    Cache, UseValue = SideValue
    Knots = UseValue.Pcurve.Knots
    if not Knots[0] <= Param <= Knots[-1]:
        raise ValueError("Fusion Form crease check found a pcurve off the edge range")
    Point, _ = CurveFrame(UseValue.Pcurve, Param)
    AlongU, AlongV = SurfaceFrame(Cache, Point[0], Point[1])
    return UnitValue(CrossValue(AlongU, AlongV))


def TurnAngle(Curve: BsCurve, Sides: list[KCreaseSide], Param: float) -> float:
    Former, Latter = sorted(Sides, key=lambda SideValue: SideValue[1].Reversed)
    First, Second = SideNormal(Former, Param), SideNormal(Latter, Param)
    Across = CrossValue(First, Second)
    SineValue = math.sqrt(sum(Entry * Entry for Entry in Across))
    Inner = sum(Entry * Other for Entry, Other in zip(First, Second))
    _, Tangent = CurveFrame(Curve, Param)
    Turning = sum(Entry * Other for Entry, Other in zip(Across, Tangent))
    return math.copysign(math.atan2(SineValue, Inner), Turning)


def InnerKnots(Curve: BsCurve, Lower: float, Upper: float) -> list[float]:
    return [KnotValue for KnotValue in Curve.Knots if Lower < KnotValue < Upper]


def SpanSamples(Measure: KCreaseTurn, Begin: float, Finish: float) -> KCreaseSpan:
    Params = [
        Begin + (Finish - Begin) * Index / KCreaseSamples
        for Index in range(KCreaseSamples + 1)
    ]
    return [(Param, Measure(Param)) for Param in Params]


def GoldenPeak(
    Measure: KCreaseTurn, Facing: float, Lower: float, Upper: float
) -> float:
    Inside = Upper - KGoldenCut * (Upper - Lower)
    Outside = Lower + KGoldenCut * (Upper - Lower)
    InsideValue, OutsideValue = Facing * Measure(Inside), Facing * Measure(Outside)
    for _ in range(KPeakSteps):
        if InsideValue >= OutsideValue:
            Upper, Outside, OutsideValue = Outside, Inside, InsideValue
            Inside = Upper - KGoldenCut * (Upper - Lower)
            InsideValue = Facing * Measure(Inside)
        else:
            Lower, Inside, InsideValue = Inside, Outside, OutsideValue
            Outside = Lower + KGoldenCut * (Upper - Lower)
            OutsideValue = Facing * Measure(Outside)
    return max(InsideValue, OutsideValue)


def PeakTurn(Measure: KCreaseTurn, Samples: KCreaseSpan, Facing: float) -> float:
    Values = [Facing * Angle for _, Angle in Samples]
    Leader = Values.index(max(Values))
    if not KFlatTurn < Values[Leader] <= KTangentTurn:
        return Values[Leader]
    Lower = Samples[max(Leader - 1, 0)][0]
    Upper = Samples[min(Leader + 1, len(Samples) - 1)][0]
    return max(Values[Leader], GoldenPeak(Measure, Facing, Lower, Upper))


def IsFlat(Samples: KCreaseSpan) -> bool:
    return all(abs(Angle) <= KFlatTurn for _, Angle in Samples)


def SpanFacing(Samples: KCreaseSpan) -> float:
    return math.copysign(1.0, max(Samples, key=lambda Entry: abs(Entry[1]))[1])


def PieceClass(Measure: KCreaseTurn, Spans: list[KCreaseSpan]) -> str:
    Samples = Spans[0][:1] + [Entry for SpanValue in Spans for Entry in SpanValue[1:]]
    Rising, Falling = PeakTurn(Measure, Samples, 1.0), PeakTurn(Measure, Samples, -1.0)
    if min(Rising, Falling) > KTangentTurn:
        raise ValueError(KCreaseFault)
    return "tangent" if max(Rising, Falling) <= KTangentTurn else "unknown"


def IsMirrored(Before: KCreaseSpan, After: KCreaseSpan) -> bool:
    Lengths = (Before[-1][0] - Before[0][0], After[-1][0] - After[0][0])
    if len(Before) != len(After) or abs(Lengths[0] - Lengths[1]) > KSeamSlack:
        return False
    return all(
        abs(Earlier[1] + Later[1]) <= KFlatTurn
        for Earlier, Later in zip(reversed(Before), After)
    )


def IsBreak(Before: KCreaseSpan, After: KCreaseSpan, Labels: list[str]) -> bool:
    if Labels == ["tangent", "tangent"]:
        return False
    if IsFlat(Before) or IsFlat(After) or SpanFacing(Before) == SpanFacing(After):
        return True
    return "tangent" not in Labels or not IsMirrored(Before, After)


def SignRoot(Measure: KCreaseTurn, Lower: float, Upper: float) -> float:
    Facing = Measure(Lower) > 0.0
    for _ in range(KRootSteps):
        Middle = 0.5 * (Lower + Upper)
        if Middle in (Lower, Upper):
            break
        Value = Measure(Middle)
        if Value == 0.0:
            return Middle
        if (Value > 0.0) == Facing:
            Lower = Middle
        else:
            Upper = Middle
    return 0.5 * (Lower + Upper)


def RootSpans(Measure: KCreaseTurn, SpanValue: KCreaseSpan) -> list[KCreaseSpan]:
    Signed = [Entry for Entry in SpanValue if abs(Entry[1]) > KFlatTurn]
    Roots = [
        SignRoot(Measure, Before[0], After[0])
        for Before, After in zip(Signed, Signed[1:])
        if (Before[1] > 0.0) != (After[1] > 0.0)
    ]
    if not Roots:
        return [SpanValue]
    Breaks = [SpanValue[0][0], *Roots, SpanValue[-1][0]]
    Parts: list[KCreaseSpan] = []
    for Index, (Begin, Finish) in enumerate(zip(Breaks, Breaks[1:])):
        Slice = SpanSamples(Measure, Begin, Finish)
        if Index > 0:
            Slice[0] = (Begin, 0.0)
        if Index < len(Roots):
            Slice[-1] = (Finish, 0.0)
        Parts.append(Slice)
    return Parts


def EdgeSpans(
    Curve: BsCurve, Sides: list[KCreaseSide], Lower: float, Upper: float
) -> list[KCreaseSpan]:
    Measure = BindArgs(TurnAngle, Curve, Sides)
    Breaks = [Lower, *InnerKnots(Curve, Lower, Upper), Upper]
    return [
        Slice
        for Begin, Finish in zip(Breaks, Breaks[1:])
        for Slice in RootSpans(Measure, SpanSamples(Measure, Begin, Finish))
    ]


def SideSamples(Spans: list[KCreaseSpan]) -> KCreaseSpan:
    return Spans[0][:1] + [Entry for SpanValue in Spans for Entry in SpanValue[1:]]


def IsRootTurned(Measure: KCreaseTurn, Spans: list[KCreaseSpan], Index: int) -> bool:
    Sides = ((Spans[max(Index - 2, 0) : Index], -1), (Spans[Index : Index + 2], 0))
    return all(
        PeakTurn(Measure, SideSamples(SideSpans), SpanFacing(SideSpans[Inner]))
        > KTangentTurn
        for SideSpans, Inner in Sides
    )


def IsJoined(
    Measure: KCreaseTurn,
    Spans: list[KCreaseSpan],
    Index: int,
    Labels: list[str],
    Knots: tuple[float, ...],
) -> bool:
    if Spans[Index][0][0] in Knots:
        return not IsBreak(Spans[Index - 1], Spans[Index], Labels)
    if "tangent" in Labels:
        return True
    if not IsRootTurned(Measure, Spans, Index):
        raise ValueError(KCreaseFault)
    return False


def IsWideRoot(
    Measure: KCreaseTurn,
    Spans: list[KCreaseSpan],
    Index: int,
    Knots: tuple[float, ...],
) -> bool:
    Labels = [PieceClass(Measure, Spans[:Index]), PieceClass(Measure, Spans[Index:])]
    if Spans[Index][0][0] in Knots or "tangent" in Labels:
        return False
    return not IsRootTurned(Measure, Spans, Index)


def IsHalving(Places: list[float]) -> bool:
    if len(Places) <= KEndReach + 1:
        return False
    Width = Places[KEndReach] - Places[0]
    return all(
        abs(Places[0] + Width / Parts - Place) <= KSeamSlack * max(1.0, abs(Width))
        for Parts, Place in zip(KEndHalves, Places[1:KEndReach])
    )


def CageKnots(Knots: tuple[float, ...], Lower: float, Upper: float) -> list[float]:
    Places = [
        Lower,
        *sorted({Value for Value in Knots if Lower < Value < Upper}),
        Upper,
    ]
    if IsHalving(Places):
        Places = Places[:1] + Places[KEndReach:]
    if IsHalving([-Value for Value in reversed(Places)]):
        Places = Places[:-KEndReach] + Places[-1:]
    return Places


def ChordLength(Curve: BsCurve, Begin: float, Finish: float) -> float:
    Start, _ = CurveFrame(Curve, Begin)
    Close, _ = CurveFrame(Curve, Finish)
    return math.dist(Start, Close)


def IsSteep(Curve: BsCurve, Spans: list[KCreaseSpan]) -> bool:
    Pairs = [Couple for SpanValue in Spans for Couple in zip(SpanValue, SpanValue[1:])]
    ByParam = any(
        abs(Later[1] - Earlier[1]) > KTurnRate * (Later[0] - Earlier[0])
        for Earlier, Later in Pairs
    )
    ByLength = any(
        abs(Later[1] - Earlier[1])
        > KTurnRate * ChordLength(Curve, Earlier[0], Later[0])
        for Earlier, Later in Pairs
    )
    if ByParam != ByLength:
        raise ValueError(KCreaseFault)
    return ByParam


def KnotSpans(
    Measure: KCreaseTurn, Places: list[float], Place: int
) -> list[KCreaseSpan]:
    Nudge = min(Later - Earlier for Earlier, Later in zip(Places, Places[1:]))
    Nudge /= KCreaseSamples
    return [
        [
            (Param, Measure(Param))
            for Param in (max(Places[0], Joint - Nudge), min(Places[-1], Joint + Nudge))
        ]
        for Joint in Places[Place : Place + 2]
    ]


def IsCalm(
    Measure: KCreaseTurn, Spans: list[KCreaseSpan], Begin: float, Finish: float
) -> bool:
    Samples = [
        Entry
        for Entry in SideSamples(Spans)
        if Begin - KSeamSlack <= Entry[0] <= Finish + KSeamSlack
    ]
    Rising, Falling = PeakTurn(Measure, Samples, 1.0), PeakTurn(Measure, Samples, -1.0)
    return max(Rising, Falling) <= KTangentTurn


def RunEnds(
    Measure: KCreaseTurn,
    Spans: list[KCreaseSpan],
    Places: list[float],
    Anchor: tuple[int, float],
) -> tuple[int, int]:
    Place, Center = Anchor
    Opening, Closing = Place, Place + 1
    while Opening >= 0 and IsCalm(Measure, Spans, Places[Opening], Center):
        Opening -= 1
    while Closing < len(Places) and IsCalm(Measure, Spans, Center, Places[Closing]):
        Closing += 1
    if Opening == Place or Closing == Place + 1:
        raise ValueError(KCreaseFault)
    return Opening + 1, Closing - 1


def TurnExcess(Measure: KCreaseTurn, Param: float) -> float:
    return abs(Measure(Param)) - KTangentTurn


def CrossPlace(
    Measure: KCreaseTurn, Spans: list[KCreaseSpan], Index: int, Toward: float
) -> float:
    Samples = SideSamples(Spans[:Index] if Toward < 0.0 else Spans[Index:])
    Outside = [
        Order for Order, Entry in enumerate(Samples) if abs(Entry[1]) > KTangentTurn
    ]
    if not Outside:
        raise ValueError(KCreaseFault)
    Order = max(Outside) if Toward < 0.0 else min(Outside)
    Bounds = sorted((Samples[Order][0], Samples[Order - int(Toward)][0]))
    return SignRoot(BindArgs(TurnExcess, Measure), Bounds[0], Bounds[1])


def LeanSign(
    Measure: KCreaseTurn, Spans: list[KCreaseSpan], Index: int, Reach: float
) -> float:
    Nudge = KSeamSlack * Reach
    Rates = [
        abs(Measure(Place + Nudge) - Measure(Place - Nudge))
        for Place in (
            CrossPlace(Measure, Spans, Index, -1.0),
            CrossPlace(Measure, Spans, Index, 1.0),
        )
    ]
    if not max(Rates):
        raise ValueError(KCreaseFault)
    Slant = (Rates[1] - Rates[0]) / max(Rates)
    if abs(Slant) <= KTangentTurn * KTangentTurn:
        return 0.0
    return math.copysign(1.0, Slant)


def LeftChoice(
    Leaning: float,
    IsLeftSteep: Callable[[], bool],
    Bounded: bool,
    Marks: tuple[float, KCreaseMark],
) -> KCreaseMark:
    if Leaning < 0.0 or IsLeftSteep():
        return Marks[1]
    if Bounded or Leaning > 0.0:
        return None
    return Marks[0]


def RightChoice(
    Leaning: float,
    Steeps: tuple[Callable[[], bool], Callable[[], bool]],
    Marks: tuple[float, KCreaseMark],
) -> KCreaseMark:
    if Leaning > 0.0 or Steeps[1]():
        return Marks[1]
    if Leaning == 0.0:
        return Marks[0]
    if Steeps[0]():
        return None
    raise ValueError(KCreaseFault)


def RootSplit(
    Curve: BsCurve,
    Measure: KCreaseTurn,
    Spans: list[KCreaseSpan],
    Index: int,
    Knots: tuple[float, ...],
) -> KCreaseMark:
    Places = CageKnots(Knots, Spans[0][0][0], Spans[-1][-1][0])
    Center = Spans[Index][0][0]
    Place = max(Order for Order, Value in enumerate(Places) if Value < Center)
    Opening, Closing = RunEnds(Measure, Spans, Places, (Place, Center))
    Inner = (
        Places[Opening + 1] if Opening < Place else None,
        Places[Closing - 1] if Closing > Place + 1 else None,
    )
    if IsSteep(Curve, KnotSpans(Measure, Places, Place)):
        return Inner[0]
    Leaning = LeanSign(Measure, Spans, Index, Places[-1] - Places[0])
    Steeps = (
        BindArgs(IsSteep, Curve, Spans[:Index]),
        BindArgs(IsSteep, Curve, Spans[Index:]),
    )
    Bounded = Closing == len(Places) - 2
    if Opening == 1:
        return LeftChoice(Leaning, Steeps[0], Bounded, (Places[1], Inner[0]))
    if Bounded:
        return RightChoice(Leaning, Steeps, (Places[Closing], Inner[1]))
    if Leaning:
        raise ValueError(KCreaseFault)
    return None


def WidePieces(
    Curve: BsCurve,
    Measure: KCreaseTurn,
    Spans: list[KCreaseSpan],
    Index: int,
    Knots: tuple[float, ...],
) -> list[KCreasePiece]:
    Marker = RootSplit(Curve, Measure, Spans, Index, Knots)
    Cutting = Index
    if Marker is not None:
        Found = [
            Order for Order, SpanValue in enumerate(Spans) if SpanValue[0][0] == Marker
        ]
        if not Found:
            raise ValueError(KCreaseFault)
        Cutting = Found[0]
    return [
        (PartSpans[0][0][0], PartSpans[-1][-1][0], PieceClass(Measure, PartSpans))
        for PartSpans in (Spans[:Cutting], Spans[Cutting:])
    ]


def IsBothMarked(Values: list[float], Lower: float, Upper: float) -> bool:
    Width = Upper - Lower
    Slack = KSeamSlack * max(1.0, abs(Width))
    Targets = [
        Place
        for Parts in KEndHalves
        for Place in (Lower + Width / Parts, Upper - Width / Parts)
    ]
    Inner = [Value for Value in Values if Lower < Value < Upper]
    if any(all(abs(Target - Value) > Slack for Target in Targets) for Value in Inner):
        return False
    return all(
        any(abs(Target - Value) <= Slack for Value in Inner) for Target in Targets[:4]
    )


def IsTwoEnded(Knots: tuple[float, ...], Place: float) -> bool:
    Values = sorted(set(Knots))
    return any(
        IsBothMarked(Values, Lower, Upper)
        for Lower in Values
        if Lower < Place
        for Upper in Values
        if Upper > Place
    )


def CheckCuts(
    Pieces: list[KCreasePiece], Knots: tuple[float, ...], Skipped: tuple[float, ...]
) -> list[KCreasePiece]:
    for Piece in Pieces[:-1]:
        if Piece[1] not in Skipped and IsTwoEnded(Knots, Piece[1]):
            raise ValueError(KCreaseFault)
    return Pieces


def SpanPieces(
    Measure: KCreaseTurn,
    Spans: list[KCreaseSpan],
    Knots: tuple[float, ...],
    Curve: BsCurve | None = None,
) -> list[KCreasePiece]:
    Starts = [0] + [
        Index for Index in range(1, len(Spans)) if abs(Spans[Index][0][1]) <= KFlatTurn
    ]
    if len(Starts) == 2 and Curve is not None:
        if IsWideRoot(Measure, Spans, Starts[1], Knots):
            WideCut = WidePieces(Curve, Measure, Spans, Starts[1], Knots)
            return CheckCuts(WideCut, Knots, ())
    Pieces: list[tuple[list[KCreaseSpan], str]] = []
    for Start, Final in zip(Starts, Starts[1:] + [len(Spans)]):
        Group = Spans[Start:Final]
        Label = PieceClass(Measure, Group)
        Labels = [Pieces[-1][1], Label] if Pieces else []
        if Pieces and IsJoined(Measure, Spans, Start, Labels, Knots):
            Merged = Pieces[-1][0] + Group
            Pieces[-1] = (Merged, PieceClass(Measure, Merged))
        else:
            Pieces.append((Group, Label))
    Found = [(Group[0][0][0], Group[-1][-1][0], Label) for Group, Label in Pieces]
    return CheckCuts(Found, Knots, Knots)


def EdgeRange(EdgeValue: FormEdge) -> tuple[float, float]:
    Knots = EdgeValue.Curve.Knots
    return EdgeValue.Bounds or (Knots[0], Knots[-1])


def SeamMove(Values: list[float], Toward: float, Lower: float, Upper: float) -> float:
    if Toward < 0.0 and all(abs(Value - Lower) <= KSeamSlack for Value in Values):
        return Upper - Lower
    if Toward > 0.0 and all(abs(Value - Upper) <= KSeamSlack for Value in Values):
        return Lower - Upper
    return 0.0


def InsideUse(Cache: NubsSurface, UseValue: FormUse) -> FormUse:
    Poles = UseValue.Pcurve.Poles
    Sense = -1.0 if UseValue.Reversed else 1.0
    StepU = (Poles[-1][0] - Poles[0][0]) * Sense
    StepV = (Poles[-1][1] - Poles[0][1]) * Sense
    MoveU = SeamMove(
        [PoleValue[0] for PoleValue in Poles],
        -StepV,
        Cache.KnotsU[0].Value,
        Cache.KnotsU[-1].Value,
    )
    MoveV = SeamMove(
        [PoleValue[1] for PoleValue in Poles],
        StepU,
        Cache.KnotsV[0].Value,
        Cache.KnotsV[-1].Value,
    )
    if not MoveU and not MoveV:
        return UseValue
    Moved = tuple(
        (PoleValue[0] + MoveU, PoleValue[1] + MoveV, *PoleValue[2:])
        for PoleValue in Poles
    )
    return ReplaceValue(UseValue, Pcurve=ReplaceValue(UseValue.Pcurve, Poles=Moved))


def EdgeSides(BodyValue: FormBody) -> dict[int, list[KCreaseSide]]:
    Sides: dict[int, list[KCreaseSide]] = {}
    for FaceValue in BodyValue.Faces:
        for UseValue in FaceValue.Uses:
            Entry = (
                FaceValue.Surface.Cache,
                InsideUse(FaceValue.Surface.Cache, UseValue),
            )
            Sides.setdefault(UseValue.EdgeIndex, []).append(Entry)
    return Sides


def CurveGroups(
    BodyValue: FormBody, Sides: dict[int, list[KCreaseSide]]
) -> list[list[int]]:
    Groups: dict[BsCurve, list[int]] = {}
    for EdgeIndex, EdgeValue in enumerate(BodyValue.Edges):
        if len(Sides.get(EdgeIndex, [])) != 2:
            continue
        if EdgeValue.Convexity not in ("tangent", "unknown"):
            raise ValueError("Fusion Form crease check needs tangent or unknown edges")
        Groups.setdefault(EdgeValue.Curve, []).append(EdgeIndex)
    return [
        sorted(Members, key=lambda Place: EdgeRange(BodyValue.Edges[Place])[0])
        for Members in Groups.values()
    ]


def GroupPieces(
    BodyValue: FormBody, Sides: dict[int, list[KCreaseSide]], Members: list[int]
) -> list[list[KCreasePiece]]:
    Curve = BodyValue.Edges[Members[0]].Curve
    Ranges = [EdgeRange(BodyValue.Edges[Place]) for Place in Members]
    Spans = [
        EdgeSpans(Curve, Sides[Place], Lower, Upper)
        for Place, (Lower, Upper) in zip(Members, Ranges)
    ]
    Found = [
        SpanPieces(
            BindArgs(TurnAngle, Curve, Sides[Place]),
            MemberSpans,
            Curve.Knots,
            Curve=Curve,
        )
        for Place, MemberSpans in zip(Members, Spans)
    ]
    for Index in range(len(Members) - 1):
        Joint = Ranges[Index][1]
        Before, After = Spans[Index][-1], Spans[Index + 1][0]
        Labels = [Found[Index][-1][2], Found[Index + 1][0][2]]
        if (
            Ranges[Index + 1][0] != Joint
            or Joint not in Curve.Knots
            or not IsFlat(Before[-1:])
            or not IsBreak(Before, After, Labels)
        ):
            raise ValueError(KCreaseFault)
    return Found


def LeadReversed(BodyValue: FormBody) -> frozenset[int]:
    Found: dict[int, bool] = {}
    for FaceValue in BodyValue.Faces:
        for UseValue in FaceValue.Uses:
            _ = Found.setdefault(UseValue.EdgeIndex, UseValue.Reversed)
    return frozenset(Index for Index, Backward in Found.items() if Backward)


def SplitEdgeMut(
    EdgeValue: FormEdge, Pieces: list[KCreasePiece], Points: list[KJournalVector]
) -> list[FormEdge]:
    if len(Pieces) == 1:
        return [ReplaceValue(EdgeValue, Convexity=Pieces[0][2])]
    VertexEnds = [EdgeValue.StartVertex]
    for _, Upper, _ in Pieces[:-1]:
        Point, _ = CurveFrame(EdgeValue.Curve, Upper)
        VertexEnds.append(len(Points))
        Points.append((Point[0], Point[1], Point[2]))
    VertexEnds.append(EdgeValue.EndVertex)
    return [
        ReplaceValue(
            EdgeValue,
            StartVertex=VertexEnds[Index],
            EndVertex=VertexEnds[Index + 1],
            Convexity=Label,
            Bounds=(Lower, Upper),
        )
        for Index, (Lower, Upper, Label) in enumerate(Pieces)
    ]


def OrderPoints(
    Points: list[KJournalVector], Edges: list[FormEdge]
) -> tuple[tuple[KJournalVector, ...], tuple[FormEdge, ...]]:
    Order: dict[int, int] = {}
    for EdgeValue in Edges:
        _ = Order.setdefault(EdgeValue.StartVertex, len(Order))
        _ = Order.setdefault(EdgeValue.EndVertex, len(Order))
    if len(Order) != len(Points):
        raise ValueError("Fusion Form conversion found a vertex off every edge")
    Placed = list(Points)
    for Former, Latter in Order.items():
        Placed[Latter] = Points[Former]
    Renamed = tuple(
        ReplaceValue(
            EdgeValue,
            StartVertex=Order[EdgeValue.StartVertex],
            EndVertex=Order[EdgeValue.EndVertex],
        )
        for EdgeValue in Edges
    )
    return tuple(Placed), Renamed


def SplitUses(FaceValue: FormFace, Places: list[list[int]]) -> FormFace:
    UseList = tuple(
        ReplaceValue(UseValue, EdgeIndex=Place)
        for UseValue in FaceValue.Uses
        for Place in (
            reversed(Places[UseValue.EdgeIndex])
            if UseValue.Reversed
            else Places[UseValue.EdgeIndex]
        )
    )
    return ReplaceValue(FaceValue, Uses=UseList)


def ClassifyEdges(BodyValue: FormBody) -> FormBody:
    Sides = EdgeSides(BodyValue)
    Found: dict[int, list[KCreasePiece]] = {}
    for Members in CurveGroups(BodyValue, Sides):
        Found.update(zip(Members, GroupPieces(BodyValue, Sides, Members)))
    Points = list(BodyValue.PointsCm)
    Backwards = LeadReversed(BodyValue)
    Edges: list[FormEdge] = []
    Places: list[list[int]] = []
    for EdgeIndex, EdgeValue in enumerate(BodyValue.Edges):
        Pieces = Found.get(EdgeIndex)
        Backward = EdgeIndex in Backwards
        Parts = (
            [EdgeValue] if Pieces is None else SplitEdgeMut(EdgeValue, Pieces, Points)
        )
        Indices = list(range(len(Edges), len(Edges) + len(Parts)))
        Places.append(Indices[::-1] if Backward else Indices)
        Edges += Parts[::-1] if Backward else Parts
    Faces = tuple(SplitUses(FaceValue, Places) for FaceValue in BodyValue.Faces)
    Placed, Renamed = OrderPoints(Points, Edges)
    return ReplaceValue(BodyValue, PointsCm=Placed, Edges=Renamed, Faces=Faces)
