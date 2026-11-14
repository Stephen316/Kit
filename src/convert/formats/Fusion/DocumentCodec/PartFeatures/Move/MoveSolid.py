from dataclasses import replace as ReplaceValue
from math import cos as Cosine, radians as Radians, sin as SineOf

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)

KMoveFrame = tuple[float, float, float, float, float]
KQuarterTurns = {0: (1.0, 0.0), 90: (0.0, 1.0), 180: (-1.0, 0.0), 270: (0.0, -1.0)}


def MoveFrame(Feature: MoveSpec) -> KMoveFrame:
    Wrapped = Feature.TurnDegrees % 360.0
    Exact = KQuarterTurns.get(int(Wrapped)) if Wrapped.is_integer() else None
    Turned = Radians(Feature.TurnDegrees)
    CosValue, SinValue = Exact or (Cosine(Turned), SineOf(Turned))
    ShiftX, ShiftY = Feature.OffsetMm[0] / 10.0, Feature.OffsetMm[1] / 10.0
    return CosValue, SinValue, ShiftX, ShiftY, Turned


def MovePoint(Point: tuple[float, float], Frame: KMoveFrame) -> tuple[float, float]:
    CosValue, SinValue, ShiftX, ShiftY, _ = Frame
    return (
        Point[0] * CosValue - Point[1] * SinValue + ShiftX,
        Point[0] * SinValue + Point[1] * CosValue + ShiftY,
    )


def MoveSpan(Value: KPlaneSpan, Frame: KMoveFrame) -> KPlaneSpan:
    if isinstance(Value, LineSpan):
        Start, Finish = MovePoint(Value.StartCm, Frame), MovePoint(
            Value.FinishCm, Frame
        )
        return LineSpan(Start, Finish, Value.Label)
    Center = MovePoint(Value.CenterCm, Frame)
    Opening = Value.StartAngle + Frame[4]
    return ArcSpan(Center, Value.RadiusCm, Opening, Value.SweepAngle, Value.Label)


def MoveLoops(
    Loops: tuple[KPlaneLoop, ...], Frame: KMoveFrame
) -> tuple[KPlaneLoop, ...]:
    return tuple(
        tuple(MoveSpan(Value, Frame) for Value in LoopValue) for LoopValue in Loops
    )


def MoveSolid(Solid: PrismSolid, Feature: MoveSpec) -> PrismSolid:
    Frame = MoveFrame(Feature)
    LiftCm = Feature.OffsetMm[2] / 10.0
    Slabs = tuple(
        PrismSlab(
            SlabValue.LowerCm + LiftCm,
            SlabValue.UpperCm + LiftCm,
            MoveLoops(SlabValue.Loops, Frame),
            SlabValue.FloorLabel,
            SlabValue.RoofLabel,
            MoveLoops(SlabValue.RoofLoops, Frame),
        )
        for SlabValue in Solid.Slabs
    )
    Edges = tuple(
        (Owner, Level + LiftCm, RimLabel) for Owner, Level, RimLabel in Solid.EdgeTags
    )
    return ReplaceValue(Solid, Slabs=Slabs, EdgeTags=Edges)
