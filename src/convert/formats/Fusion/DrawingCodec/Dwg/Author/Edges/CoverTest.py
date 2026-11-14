from math import acos as ArcCosine
from math import atan2 as ArcTangent
from math import hypot as Distance

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.EdgeVectors import (
    KFullTurn,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.PathPoints import (
    PathPoint,
    PathTangent,
    RoundPoint,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import (
    KPointPair,
    KPointTriple,
    LinePath,
    RoundPath,
    SolidEdge,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    DotProduct,
    ViewFrame,
)

KCoverGap = 1e-6
KDepthGap = 1e-6
KParallel = 1e-6
KSweepGap = 1e-9
KSelfGap = 1e-7
KEdgeOnGap = 1e-9


def FlatOf(Frame: ViewFrame, Point: KPointTriple) -> KPointPair:
    return (DotProduct(Point, Frame.Right), DotProduct(Point, Frame.Up))


def DepthOf(Frame: ViewFrame, Point: KPointTriple) -> float:
    return DotProduct(Point, Frame.Eye)


def IsParallel(First: KPointPair, Second: KPointPair) -> bool:
    Former, Latter = Distance(*First), Distance(*Second)
    if Former < KEdgeOnGap or Latter < KEdgeOnGap:
        return False
    return (
        abs(First[0] * Second[1] - First[1] * Second[0]) <= KParallel * Former * Latter
    )


def IsLineCover(
    Frame: ViewFrame,
    Curve: LinePath,
    Sighted: KPointPair,
    Heading: KPointPair,
    Depth: float,
) -> bool:
    Lower, Upper = FlatOf(Frame, Curve.Start), FlatOf(Frame, Curve.Finish)
    SpanFlat = (Upper[0] - Lower[0], Upper[1] - Lower[1])
    Square = SpanFlat[0] ** 2 + SpanFlat[1] ** 2
    if Square < KEdgeOnGap**2 or not IsParallel(Heading, SpanFlat):
        return False
    Share = (
        (Sighted[0] - Lower[0]) * SpanFlat[0] + (Sighted[1] - Lower[1]) * SpanFlat[1]
    ) / Square
    if not -KSweepGap <= Share <= 1 + KSweepGap:
        return False
    Apart = Distance(
        Lower[0] + Share * SpanFlat[0] - Sighted[0],
        Lower[1] + Share * SpanFlat[1] - Sighted[1],
    )
    Nearer = DepthOf(Frame, PathPoint(Curve, Share)) > Depth + KDepthGap
    return Apart <= KCoverGap and Nearer


def RoundAngles(
    Frame: ViewFrame, Curve: RoundPath, Sighted: KPointPair
) -> tuple[float, ...]:
    Across, Upward = FlatOf(Frame, Curve.XAxis), FlatOf(Frame, Curve.YAxis)
    Middle = FlatOf(Frame, Curve.Center)
    ShiftX = (Sighted[0] - Middle[0]) / Curve.Radius
    ShiftY = (Sighted[1] - Middle[1]) / Curve.Radius
    Divisor = Across[0] * Upward[1] - Across[1] * Upward[0]
    if abs(Divisor) > KEdgeOnGap:
        CosPart = (ShiftX * Upward[1] - ShiftY * Upward[0]) / Divisor
        SinPart = (Across[0] * ShiftY - Across[1] * ShiftX) / Divisor
        return (ArcTangent(SinPart, CosPart),)
    Longer = Across if Distance(*Across) >= Distance(*Upward) else Upward
    Scale = Distance(*Longer)
    Toward = (Longer[0] / Scale, Longer[1] / Scale)
    Alpha = Across[0] * Toward[0] + Across[1] * Toward[1]
    BetaPart = Upward[0] * Toward[0] + Upward[1] * Toward[1]
    Ratio = (ShiftX * Toward[0] + ShiftY * Toward[1]) / Distance(Alpha, BetaPart)
    if abs(Ratio) > 1 + KSweepGap:
        return ()
    Halfway = ArcCosine(max(-1.0, min(1.0, Ratio)))
    Phase = ArcTangent(BetaPart, Alpha)
    return (Phase + Halfway, Phase - Halfway)


def IsSameAngle(First: float, Second: float) -> bool:
    return abs((First - Second + KFullTurn / 2) % KFullTurn - KFullTurn / 2) < KSelfGap


def IsRoundCover(
    Frame: ViewFrame,
    Curve: RoundPath,
    Sighted: KPointPair,
    Heading: KPointPair,
    Depth: float,
    Itself: float | None,
) -> bool:
    for Angle in RoundAngles(Frame, Curve, Sighted):
        if (Angle - Curve.Opening) % KFullTurn > Curve.Sweep + KSweepGap:
            continue
        if Itself is not None and IsSameAngle(Angle, Itself):
            continue
        Point = RoundPoint(Curve, Angle)
        Projected = FlatOf(Frame, Point)
        if Distance(Projected[0] - Sighted[0], Projected[1] - Sighted[1]) > KCoverGap:
            continue
        Param = ((Angle - Curve.Opening) % KFullTurn) / Curve.Sweep
        Turning = FlatOf(Frame, PathTangent(Curve, min(Param, 1.0)))
        if IsParallel(Heading, Turning) and DepthOf(Frame, Point) > Depth + KDepthGap:
            return True
    return False


def IsCovered(
    Frame: ViewFrame, Candidates: tuple[SolidEdge, ...], Index: int, Param: float
) -> bool:
    Curve = Candidates[Index].Curve
    Point = PathPoint(Curve, Param)
    Sighted = FlatOf(Frame, Point)
    Heading = FlatOf(Frame, PathTangent(Curve, Param))
    Depth = DepthOf(Frame, Point)
    for Other, Entry in enumerate(Candidates):
        if isinstance(Entry.Curve, LinePath):
            if Other != Index and IsLineCover(
                Frame, Entry.Curve, Sighted, Heading, Depth
            ):
                return True
            continue
        Itself = None
        if Other == Index:
            Itself = Entry.Curve.Opening + Param * Entry.Curve.Sweep
        if IsRoundCover(Frame, Entry.Curve, Sighted, Heading, Depth, Itself):
            return True
    return False


def FlatSpan(Frame: ViewFrame, Curve: LinePath | RoundPath) -> float:
    if isinstance(Curve, RoundPath):
        return Curve.Radius
    Lower, Upper = FlatOf(Frame, Curve.Start), FlatOf(Frame, Curve.Finish)
    return Distance(Upper[0] - Lower[0], Upper[1] - Lower[1])
