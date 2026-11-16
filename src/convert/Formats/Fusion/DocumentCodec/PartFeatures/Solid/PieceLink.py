from math import atan2 as ArcTangent, hypot as Hypotenuse

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.OffsetMath import KPoint
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    KFullTurn,
    SpanFinish,
    SpanHeading,
    SpanStart,
)

# the link limit tolerance prevents rounding noise from creating false geometric distinctions during reconstruction
KLinkLimit = 1e-7


# the near decision must stay consistent so body topology remains consistent with its modeling operation
def IsNear(First: KPoint, Second: KPoint) -> bool:
    return Hypotenuse(First[0] - Second[0], First[1] - Second[1]) < KLinkLimit


# the turn angle contract needs a shared interpretation so body topology remains consistent with its modeling operation
def TurnAngle(Before: KPlaneSpan, After: KPlaneSpan) -> float:
    InwardX, InwardY = SpanHeading(Before, True)
    OutwardX, OutwardY = SpanHeading(After, False)
    return ArcTangent(
        InwardX * OutwardY - InwardY * OutwardX, InwardX * OutwardX + InwardY * OutwardY
    )


# next piece needs an explicit validity boundary so body topology remains consistent with its modeling operation
def NextPiece(Pieces: list[KPlaneSpan], Chain: list[int], Taken: set[int]) -> int:
    Latest = Pieces[Chain[-1]]
    Finish = SpanFinish(Latest)
    Options = [
        Index
        for Index, Value in enumerate(Pieces)
        if (Index not in Taken or Index == Chain[0])
        and IsNear(SpanStart(Value), Finish)
    ]
    if not Options:
        raise ValueError("Fusion part region boundary is open")

    # ordering by turn angle latest pieces index must stay deterministic so solid feature construction resolves equivalent inputs consistently
    return max(Options, key=lambda Index: TurnAngle(Latest, Pieces[Index]))


# the same carrier decision must stay consistent so body topology remains consistent with its modeling operation
def IsSameCarrier(Before: KPlaneSpan, After: KPlaneSpan) -> bool:
    if Before.Label != After.Label:
        return False
    if isinstance(Before, LineSpan) and isinstance(After, LineSpan):
        return abs(TurnAngle(Before, After)) < 1e-9
    if isinstance(Before, ArcSpan) and isinstance(After, ArcSpan):
        return (
            IsNear(Before.CenterCm, After.CenterCm)
            and abs(Before.RadiusCm - After.RadiusCm) < KLinkLimit
            and (Before.SweepAngle > 0) == (After.SweepAngle > 0)
        )
    return False


# the join pair contract needs a stable decomposition so body topology remains consistent with its modeling operation
def JoinPair(Before: KPlaneSpan, After: KPlaneSpan) -> KPlaneSpan:
    if isinstance(Before, LineSpan) and isinstance(After, LineSpan):
        return LineSpan(Before.StartCm, After.FinishCm, Before.Label)
    if not isinstance(Before, ArcSpan) or not isinstance(After, ArcSpan):
        raise ValueError("Fusion part region pieces do not share a carrier")
    Sweep = Before.SweepAngle + After.SweepAngle
    if abs(abs(Sweep) - KFullTurn) < 1e-9:
        Sweep = KFullTurn if Sweep > 0 else -KFullTurn
    return ArcSpan(
        Before.CenterCm, Before.RadiusCm, Before.StartAngle, Sweep, Before.Label
    )


# the merge runs contract needs a stable decomposition so body topology remains consistent with its modeling operation
def MergeRuns(Spans: list[KPlaneSpan]) -> KPlaneLoop:
    Merged: list[KPlaneSpan] = []
    for Value in Spans:
        if Merged and IsSameCarrier(Merged[-1], Value):
            Merged[-1] = JoinPair(Merged[-1], Value)
            continue
        Merged.append(Value)
    while len(Merged) > 1 and IsSameCarrier(Merged[-1], Merged[0]):
        Merged[0] = JoinPair(Merged.pop(), Merged[0])
    return tuple(Merged)


# link pieces must resolve unambiguously so body topology remains consistent with its modeling operation
def LinkPieces(Pieces: list[KPlaneSpan]) -> list[KPlaneLoop]:
    Taken: set[int] = set()
    Loops: list[KPlaneLoop] = []
    for First in range(len(Pieces)):
        if First in Taken:
            continue
        Chain = [First]
        Taken.add(First)
        while True:
            Following = NextPiece(Pieces, Chain, Taken)
            if Following == First:
                break
            Chain.append(Following)
            Taken.add(Following)
        Loops.append(MergeRuns([Pieces[Index] for Index in Chain]))
    return Loops
