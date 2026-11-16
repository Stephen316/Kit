from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import LoopArea
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.OffsetMath import KPoint
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.OpenShell import (
    IsOnSide,
    MixedJoint,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanCross import (
    SpanCross,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    SpanFinish,
    SpanHeading,
    SpanStart,
)

# the offset limit tolerance prevents rounding noise from creating false geometric distinctions during reconstruction
KOffsetLimit = 1e-7


# offset index needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def OffsetIndex(LoopValue: KPlaneLoop, PointCm: KPoint) -> int:
    Matches = [
        Index for Index, Value in enumerate(LoopValue) if IsOnSide(Value, PointCm)
    ]
    if len(Matches) != 1:
        raise ValueError("Fusion offset sides must name one straight side")
    return Matches[0]


# kept piece needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def KeptPiece(Value: KPlaneSpan, Start: KPoint, Finish: KPoint) -> LineSpan:
    HeadX, HeadY = SpanHeading(Value, False)
    Along = (Finish[0] - Start[0]) * HeadX + (Finish[1] - Start[1]) * HeadY
    if Along <= KOffsetLimit:
        raise ValueError("Fusion offset distance consumes a neighbouring side")
    return LineSpan(Start, Finish, Value.Label)


# the simple decision must stay consistent so feature parameters remain connected to the resulting geometry
def IsSimple(LoopValue: KPlaneLoop) -> bool:
    Count = len(LoopValue)
    for First in range(Count):
        for Second in range(First + 2, Count):
            if First == 0 and Second == Count - 1:
                continue
            if SpanCross(LoopValue[First], LoopValue[Second]):
                return False
    return True


# shift loop needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def ShiftLoop(LoopValue: KPlaneLoop, Index: int, DistanceCm: float) -> KPlaneLoop:
    Count = len(LoopValue)
    Before, After = (Index - 1) % Count, (Index + 1) % Count
    if Count < 3:
        raise ValueError("Fusion offset sides need two straight neighbours")
    Spans = (LoopValue[Before], LoopValue[Index], LoopValue[After])
    First = MixedJoint(Spans[0], Spans[1], (0.0, -DistanceCm))
    Second = MixedJoint(Spans[1], Spans[2], (-DistanceCm, 0.0))
    Pieces = {
        Before: KeptPiece(Spans[0], SpanStart(Spans[0]), First),
        Index: KeptPiece(Spans[1], First, Second),
        After: KeptPiece(Spans[2], Second, SpanFinish(Spans[2])),
    }
    Shifted = tuple(Pieces.get(Place, LoopValue[Place]) for Place in range(Count))
    if LoopArea(Shifted) <= KOffsetLimit or not IsSimple(Shifted):
        raise ValueError("Fusion offset distance folds the profile")
    return Shifted
