from math import atan2 as ArcTangent, cos as Cosine, sin as SineOf

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.EdgeRound import EdgeRound
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundEdges import (
    CornerFrame,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SectionMoments import (
    BlendPiece,
    GaussSpan,
    KPolynomial,
    LinePiece,
    PieceWeight,
    SectionMoments,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    DotProduct,
    KSpaceVector,
    ScaleVector,
    SubVector,
    UnitVector,
    VectorLength,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan

KMassKeys: tuple[str, ...] = (
    "volume",
    "x",
    "y",
    "z",
    "xx",
    "yy",
    "zz",
    "xy",
    "xz",
    "yz",
)
KMassPairs = {
    "x": (0,),
    "y": (1,),
    "z": (2,),
    "xx": (0, 0),
    "yy": (1, 1),
    "zz": (2, 2),
    "xy": (0, 1),
    "xz": (0, 2),
    "yz": (1, 2),
    "volume": (),
}
KAffine = tuple[float, float, float]


def TimesPoly(First: KPolynomial, Second: KPolynomial) -> KPolynomial:
    Result: KPolynomial = {}
    for (FirstX, FirstY), OneValue in First.items():
        for (SecondX, SecondY), TwoValue in Second.items():
            Powers = (FirstX + SecondX, FirstY + SecondY)
            Result[Powers] = Result.get(Powers, 0.0) + OneValue * TwoValue
    return Result


def AffinePoly(Value: KAffine) -> KPolynomial:
    return {(0, 0): Value[0], (1, 0): Value[1], (0, 1): Value[2]}


def SliceMass(
    AxisSet: tuple[KAffine, KAffine, KAffine],
    Scale: KAffine,
    Moments: KPolynomial,
) -> dict[str, float]:
    Result: dict[str, float] = {}
    for KeyValue, Indices in KMassPairs.items():
        Product = AffinePoly(Scale)
        for Index in Indices:
            Product = TimesPoly(Product, AffinePoly(AxisSet[Index]))
        Result[KeyValue] = sum(
            Amount * Moments[Powers] for Powers, Amount in Product.items()
        )
    return Result


def LineAxes(
    Frame: CornerFrame, Sense: float, Along: float, Heading: KSpaceVector
) -> tuple[KAffine, KAffine, KAffine]:
    BasePoint = tuple(Frame.Point[Index] + Heading[Index] * Along for Index in range(3))
    SideVector = ScaleVector(Frame.SideAxis, 0.0 - Sense)
    CapValue = ScaleVector(Frame.CapAxis, 0.0 - Sense)
    return (
        (BasePoint[0], SideVector[0], CapValue[0]),
        (BasePoint[1], SideVector[1], CapValue[1]),
        (BasePoint[2], SideVector[2], CapValue[2]),
    )


def MitreSlope(Frame: CornerFrame, Heading: KSpaceVector, Round: EdgeRound) -> float:
    if not Frame.Mitre:
        return 0.0
    return DotProduct(SubVector(Frame.CapPoint, Frame.Point), Heading) / Round.CapCm


def MitreMass(
    Frames: tuple[CornerFrame, CornerFrame], Sense: float, Round: EdgeRound
) -> dict[str, float]:
    Opening, Closing = Frames
    Delta = SubVector(Closing.Point, Opening.Point)
    Length, Heading = VectorLength(Delta), UnitVector(Delta)
    Leading = MitreSlope(Opening, Heading, Round)
    Spread = Leading + MitreSlope(Closing, ScaleVector(Heading, -1.0), Round)
    Moments = SectionMoments(Round)
    Scale: KAffine = (Length, 0.0 - Spread, 0.0)
    Total = dict.fromkeys(KMassKeys, 0.0)
    for Along, Weight in GaussSpan(0.0, 1.0):
        BaseRows = LineAxes(Opening, Sense, Along * Length, Heading)
        Slope = Leading - Along * Spread
        AxisSet = tuple(
            (AxisRow[0], AxisRow[1] + Heading[Index] * Slope, AxisRow[2])
            for Index, AxisRow in enumerate(BaseRows)
        )
        for KeyValue, Value in SliceMass(
            (AxisSet[0], AxisSet[1], AxisSet[2]), Scale, Moments
        ).items():
            Total[KeyValue] += Weight * Value
    Total["area"] = SweepArea(Round, Scale)
    return Total


def LineMass(
    Frames: tuple[CornerFrame, CornerFrame], Sense: float, Round: EdgeRound
) -> dict[str, float]:
    Opening, Closing = Frames
    if Opening.Mitre or Closing.Mitre:
        return MitreMass(Frames, Sense, Round)
    Delta = SubVector(Closing.Point, Opening.Point)
    Length, Heading = VectorLength(Delta), UnitVector(Delta)
    Moments = SectionMoments(Round)
    Total = dict.fromkeys(KMassKeys, 0.0)
    for Along, Weight in GaussSpan(0.0, Length):
        AxisSet = LineAxes(Opening, Sense, Along, Heading)
        for KeyValue, Value in SliceMass(AxisSet, (1.0, 0.0, 0.0), Moments).items():
            Total[KeyValue] += Weight * Value
    Total["area"] = Length * SweepArea(Round, (1.0, 0.0, 0.0))
    return Total


def SweepArea(Round: EdgeRound, Scale: KAffine) -> float:
    Weights = AffinePoly(Scale)
    Blend = PieceWeight(BlendPiece(Round), Weights)
    CapLeg = PieceWeight(LinePiece((0.0, 0.0), (Round.CapCm, 0.0)), Weights)
    WallLeg = PieceWeight(LinePiece((0.0, 0.0), (0.0, Round.WallCm)), Weights)
    return Blend - CapLeg - WallLeg


def RingAxes(
    SpanValue: ArcSpan, Frame: CornerFrame, Sense: float, Angle: float
) -> tuple[tuple[KAffine, KAffine, KAffine], KAffine]:
    Center = SpanValue.CenterCm
    Spread = Sense * (1.0 if SpanValue.SweepAngle > 0 else -1.0)
    Radius = VectorLength((Frame.Point[0] - Center[0], Frame.Point[1] - Center[1], 0.0))
    DropValue = 0.0 - Sense * Frame.CapAxis[2]
    TurnValue = (Cosine(Angle), SineOf(Angle))
    AxisSet = (
        (Center[0] + Radius * TurnValue[0], 0.0 - Spread * TurnValue[0], 0.0),
        (Center[1] + Radius * TurnValue[1], 0.0 - Spread * TurnValue[1], 0.0),
        (Frame.Point[2], 0.0, DropValue),
    )
    return AxisSet, (Radius, 0.0 - Spread, 0.0)


def RingMass(
    SpanValue: ArcSpan,
    Frame: CornerFrame,
    Turning: tuple[float, float],
    Round: EdgeRound,
) -> dict[str, float]:
    Sense, Toward = Turning
    Opening = ArcTangent(
        Frame.Point[1] - SpanValue.CenterCm[1], Frame.Point[0] - SpanValue.CenterCm[0]
    )
    Sweep = abs(SpanValue.SweepAngle)
    Closing = Opening + Toward * Sweep
    Moments = SectionMoments(Round)
    Total = dict.fromkeys(KMassKeys, 0.0)
    Scale: KAffine = (0.0, 0.0, 0.0)
    for Angle, Weight in GaussSpan(min(Opening, Closing), max(Opening, Closing)):
        AxisSet, Scale = RingAxes(SpanValue, Frame, Sense, Angle)
        for KeyValue, Value in SliceMass(AxisSet, Scale, Moments).items():
            Total[KeyValue] += Weight * Value
    Total["area"] = Sweep * SweepArea(Round, Scale)
    return Total
