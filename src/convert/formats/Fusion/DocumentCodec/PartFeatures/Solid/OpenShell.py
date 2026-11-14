from math import hypot as Hypotenuse

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.InsetLoop import InsetSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.OffsetMath import (
    KPoint,
    LineCross,
    OffsetJoint,
    TangentLine,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    SpanFinish,
    SpanHeading,
    SpanStart,
)

KOpenLimit = 1e-7


def IsOnSide(Value: KPlaneSpan, PointCm: KPoint) -> bool:
    if not isinstance(Value, LineSpan):
        return False
    (StartX, StartY), (FinishX, FinishY) = Value.StartCm, Value.FinishCm
    DeltaX, DeltaY = FinishX - StartX, FinishY - StartY
    Length = Hypotenuse(DeltaX, DeltaY)
    OffsetX, OffsetY = PointCm[0] - StartX, PointCm[1] - StartY
    Along = (OffsetX * DeltaX + OffsetY * DeltaY) / Length
    Apart = abs(OffsetX * DeltaY - OffsetY * DeltaX) / Length
    return Apart < KOpenLimit and KOpenLimit < Along < Length - KOpenLimit


def SideIndex(LoopValue: KPlaneLoop, PointCm: KPoint) -> int:
    Matches = [
        Index for Index, Value in enumerate(LoopValue) if IsOnSide(Value, PointCm)
    ]
    if len(Matches) != 1:
        raise ValueError("Fusion part shell sides must name one straight side")
    return Matches[0]


def OpenRun(LoopValue: KPlaneLoop, SidesCm: tuple[KPoint, ...]) -> tuple[int, ...]:
    Count = len(LoopValue)
    Chosen = {SideIndex(LoopValue, Point) for Point in SidesCm}
    if len(Chosen) != len(SidesCm) or len(Chosen) >= Count:
        raise ValueError("Fusion part shell sides must be distinct and keep a wall")
    Heads = [Index for Index in Chosen if (Index - 1) % Count not in Chosen]
    if len(Heads) != 1:
        raise ValueError("Fusion part shell sides must form one connected run")
    return tuple((Heads[0] + Stride) % Count for Stride in range(len(Chosen)))


def MixedJoint(
    Before: KPlaneSpan, After: KPlaneSpan, Amounts: tuple[float, float]
) -> KPoint:
    if not isinstance(Before, LineSpan) or not isinstance(After, LineSpan):
        raise ValueError("Fusion part open shell sides need straight neighbours")
    Corner = SpanFinish(Before)
    Lines = (
        TangentLine(Corner, SpanHeading(Before, True), Amounts[0]),
        TangentLine(Corner, SpanHeading(After, False), Amounts[1]),
    )
    Points = LineCross(*Lines)
    if not Points:
        raise ValueError("Fusion part offset curves do not meet")
    return Points[0]


def OpenJoints(LoopValue: KPlaneLoop, Amounts: list[float]) -> list[KPoint]:
    Joints: list[KPoint] = []
    for Index, Value in enumerate(LoopValue):
        Later = (Index + 1) % len(LoopValue)
        Amounted = (Amounts[Index], Amounts[Later])
        if Amounted[0] == Amounted[1]:
            Joints.append(OffsetJoint(Value, LoopValue[Later], Amounted[0]))
            continue
        Joints.append(MixedJoint(Value, LoopValue[Later], Amounted))
    return Joints


def SidePiece(Value: KPlaneSpan, Start: KPoint, Finish: KPoint) -> LineSpan:
    HeadX, HeadY = SpanHeading(Value, False)
    if (Finish[0] - Start[0]) * HeadX + (Finish[1] - Start[1]) * HeadY <= 1e-9:
        raise ValueError("Fusion part shell thickness consumes an open side")
    return LineSpan(Start, Finish, Value.Label)


def OpenLoop(
    LoopValue: KPlaneLoop,
    ThicknessCm: float,
    Operation: int,
    OpenSides: tuple[int, ...],
) -> KPlaneLoop:
    Count = len(LoopValue)
    Amounts = [0.0 if Index in OpenSides else ThicknessCm for Index in range(Count)]
    Joints = OpenJoints(LoopValue, Amounts)
    for Index in OpenSides:
        _ = SidePiece(LoopValue[Index], Joints[Index - 1], Joints[Index])
    First, Final = LoopValue[OpenSides[0]], LoopValue[OpenSides[-1]]
    Walls = [
        (OpenSides[-1] + Stride) % Count
        for Stride in range(1, Count - len(OpenSides) + 1)
    ]
    Cavity = tuple(
        InsetSpan(
            LoopValue[Index],
            Joints[Index - 1],
            Joints[Index],
            ThicknessCm,
            FaceLabel(
                LoopValue[Index].Label.PrimaryId,
                LoopValue[Index].Label.OperationIds + (Operation,),
            ),
        )
        for Index in reversed(Walls)
    )
    Leading = SidePiece(First, SpanStart(First), Joints[OpenSides[0] - 1])
    Trailing = SidePiece(Final, Joints[OpenSides[-1]], SpanFinish(Final))
    return (Leading, *Cavity, Trailing, *(LoopValue[Index] for Index in Walls))
