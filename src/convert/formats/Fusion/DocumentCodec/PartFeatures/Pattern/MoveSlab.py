from dataclasses import replace as ReplaceValue
from math import cos as Cosine, pi as KHalfTurn, sin as SineOf

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab

KPlacement = tuple[tuple[float, float], float, bool]


def ShiftLabel(Label: FaceLabel, Extra: tuple[int, ...]) -> FaceLabel:
    return ReplaceValue(
        Label,
        OperationIds=Label.OperationIds + Extra,
        Merged=tuple(ShiftLabel(Value, Extra) for Value in Label.Merged),
    )


def MovePoint(Point: tuple[float, float], Place: KPlacement) -> tuple[float, float]:
    (OffsetX, OffsetY), Angle, IsMirror = Place
    PointX = -Point[0] if IsMirror else Point[0]
    Turned = (
        PointX * Cosine(Angle) - Point[1] * SineOf(Angle),
        PointX * SineOf(Angle) + Point[1] * Cosine(Angle),
    )
    return Turned[0] + OffsetX, Turned[1] + OffsetY


def MoveSpan(
    Value: KPlaneSpan, Place: KPlacement, Extra: tuple[int, ...]
) -> KPlaneSpan:
    Label = ShiftLabel(Value.Label, Extra)
    if isinstance(Value, LineSpan):
        Start, Finish = MovePoint(Value.StartCm, Place), MovePoint(
            Value.FinishCm, Place
        )
        return (
            LineSpan(Finish, Start, Label)
            if Place[2]
            else LineSpan(Start, Finish, Label)
        )
    Center = MovePoint(Value.CenterCm, Place)
    Turned = Value.StartAngle + Place[1]
    if Place[2]:
        Turned = KHalfTurn - Value.StartAngle - Value.SweepAngle + Place[1]
    return ArcSpan(Center, Value.RadiusCm, Turned, Value.SweepAngle, Label)


def MoveSlab(Shaper: PrismSlab, Place: KPlacement, Extra: tuple[int, ...]) -> PrismSlab:
    Loops = tuple(
        CanonLoop(
            tuple(
                MoveSpan(Value, Place, Extra)
                for Value in (reversed(LoopValue) if Place[2] else LoopValue)
            )
        )
        for LoopValue in Shaper.Loops
    )
    return PrismSlab(
        Shaper.LowerCm,
        Shaper.UpperCm,
        Loops,
        ShiftLabel(Shaper.FloorLabel, Extra),
        ShiftLabel(Shaper.RoofLabel, Extra),
    )
