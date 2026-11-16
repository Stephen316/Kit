from dataclasses import replace as ReplaceValue
from math import hypot as Hypotenuse

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanCross import SpanCross
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    ReverseSpan,
    SpanFinish,
    SpanHeading,
    SpanStart,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Sweep.SweepPath import (
    PathSpans,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Sweep.SweepTags import (
    KFloorSide,
    KLeftSide,
    KRightSide,
    KRoofSide,
    SideLabel,
    SweepTags,
    WallLabel,
)

# clearance must remain consistent across callers so feature parameters remain connected to the resulting geometry
KClearance = 1e-7

# the joint limit tolerance prevents rounding noise from creating false geometric distinctions during reconstruction
KJointLimit = 1e-6


# the sweep profile contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def SweepProfile(Feature: SweepSpec) -> tuple[LineCurve, ...]:
    LeftMm, RightMm = Feature.LeftMm, Feature.RightMm
    Lower, Upper = 0.0 - Feature.LowerMm, 0.0 - Feature.UpperMm
    return (
        LineCurve((LeftMm, Lower), (RightMm, Lower)),
        LineCurve((RightMm, Lower), (RightMm, Upper)),
        LineCurve((RightMm, Upper), (LeftMm, Upper)),
        LineCurve((LeftMm, Upper), (LeftMm, Lower)),
    )


# offset span needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def OffsetSpan(Value: KPlaneSpan, Amount: float, Label: FaceLabel) -> KPlaneSpan:
    if isinstance(Value, LineSpan):
        HeadX, HeadY = SpanHeading(Value, False)
        ShiftX, ShiftY = HeadY * Amount, 0.0 - HeadX * Amount
        Start = (Value.StartCm[0] + ShiftX, Value.StartCm[1] + ShiftY)
        Finish = (Value.FinishCm[0] + ShiftX, Value.FinishCm[1] + ShiftY)
        return LineSpan(Start, Finish, Label)
    Sense = 1.0 if Value.SweepAngle > 0 else -1.0
    Radius = Value.RadiusCm + Amount * Sense
    if Radius <= KClearance:
        raise ValueError("Fusion sweep profiles must stay clear of path arc centres")
    return ReplaceValue(Value, RadiusCm=Radius, Label=Label)


# the near joint decision must stay consistent so feature parameters remain connected to the resulting geometry
def IsNearJoint(Point: tuple[float, float], Joints: list[tuple[float, float]]) -> bool:
    return any(
        Hypotenuse(Point[0] - Joint[0], Point[1] - Joint[1]) < KJointLimit
        for Joint in Joints
    )


# invalid crossing input must fail here so feature parameters remain connected to the resulting geometry
def CheckCrossing(LoopValue: KPlaneLoop) -> None:
    Count = len(LoopValue)
    for First in range(Count):
        for Second in range(First + 1, Count):
            Joints: list[tuple[float, float]] = []
            if Second == First + 1:
                Joints.append(SpanFinish(LoopValue[First]))
            if First == 0 and Second == Count - 1:
                Joints.append(SpanStart(LoopValue[First]))
            Points = SpanCross(LoopValue[First], LoopValue[Second])
            if not all(IsNearJoint(Point, Joints) for Point in Points):
                raise ValueError("Fusion sweep bodies must not cross themselves")


# the sweep loop contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def SweepLoop(Feature: SweepSpec, Operation: int) -> KPlaneLoop:
    Spans = PathSpans(Feature)
    TagMap = SweepTags(len(Spans))
    RightCm, LeftCm = Feature.RightMm / 10.0, Feature.LeftMm / 10.0
    Outer = tuple(
        OffsetSpan(Value, RightCm, WallLabel(TagMap, KRightSide, Place, Operation))
        for Place, Value in enumerate(Spans)
    )
    Inner = tuple(
        OffsetSpan(Value, LeftCm, WallLabel(TagMap, KLeftSide, Place, Operation))
        for Place, Value in enumerate(Spans)
    )
    Finish = LineSpan(
        SpanFinish(Outer[-1]), SpanFinish(Inner[-1]), FaceLabel("2", (Operation,))
    )
    Start = LineSpan(
        SpanStart(Inner[0]), SpanStart(Outer[0]), FaceLabel("1", (Operation,))
    )
    Returns = tuple(ReverseSpan(Value) for Value in reversed(Inner))
    LoopValue = CanonLoop((*Outer, Finish, *Returns, Start))
    CheckCrossing(LoopValue)
    return LoopValue


# the sweep solid contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def SweepSolid(Feature: SweepSpec, Operation: int) -> PrismSolid:
    LoopValue = SweepLoop(Feature, Operation)
    TagMap = SweepTags(len(Feature.Path))
    Floor = SideLabel(TagMap, KFloorSide, Operation)
    Ceiling = SideLabel(TagMap, KRoofSide, Operation)
    Bounds = (Feature.LowerMm / 10.0, Feature.UpperMm / 10.0)
    SlabValue = PrismSlab(*Bounds, (LoopValue,), Floor, Ceiling)
    BodyLabel = FaceLabel(str(Operation), (), len(TagMap) + len(Feature.Path) + 3)
    return PrismSolid((SlabValue,), BodyLabel, Sealed=True)
