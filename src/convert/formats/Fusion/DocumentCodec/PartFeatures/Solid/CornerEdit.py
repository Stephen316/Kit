from math import (
    acos as ArcCosine,
    hypot as Hypotenuse,
    pi as KHalfTurn,
    sin as SineOf,
    tan as Tangent,
)

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    PointAngle,
    SpanHeading,
    SpanLength,
)


def CornerIndex(LoopValue: KPlaneLoop, CornerCm: tuple[float, float]) -> int | None:
    for Index, Value in enumerate(LoopValue):
        Finish = Value.FinishCm if isinstance(Value, LineSpan) else None
        if (
            Finish is not None
            and Hypotenuse(Finish[0] - CornerCm[0], Finish[1] - CornerCm[1]) < 1e-7
        ):
            return Index
    return None


def CornerReach(
    AmountCm: float, Rounded: bool, Bevel: tuple[float, float], TurnAngle: float
) -> tuple[float, float]:
    if Rounded:
        Reach = AmountCm * Tangent(TurnAngle / 2.0)
        return Reach, Reach
    SecondCm, AngleRad = Bevel
    if SecondCm > 0:
        return AmountCm, SecondCm
    if AngleRad <= 0:
        return AmountCm, AmountCm
    Opening = KHalfTurn - TurnAngle
    if Opening + AngleRad >= KHalfTurn - 1e-9:
        raise ValueError("Fusion chamfer angle does not meet the adjacent side")
    return AmountCm, AmountCm * SineOf(AngleRad) / SineOf(Opening + AngleRad)


def CornerEdit(
    LoopValue: KPlaneLoop,
    Index: int,
    AmountCm: float,
    Label: FaceLabel,
    Shape: tuple[bool, tuple[float, float]],
) -> KPlaneLoop:
    Rounded, Bevel = Shape
    Before, After = LoopValue[Index], LoopValue[(Index + 1) % len(LoopValue)]
    if not isinstance(Before, LineSpan) or not isinstance(After, LineSpan):
        raise ValueError("Fusion part corner edits require two straight sides")
    InwardX, InwardY = SpanHeading(Before, True)
    OutwardX, OutwardY = SpanHeading(After, False)
    if InwardX * OutwardY - InwardY * OutwardX <= 1e-9:
        raise ValueError("Fusion part corner edits require a convex corner")
    TurnAngle = ArcCosine(max(-1.0, min(1.0, InwardX * OutwardX + InwardY * OutwardY)))
    Reach, Other = CornerReach(AmountCm, Rounded, Bevel, TurnAngle)
    if Reach >= SpanLength(Before) - 1e-9 or Other >= SpanLength(After) - 1e-9:
        raise ValueError("Fusion part corner edit exceeds the adjacent side length")
    Corner = Before.FinishCm
    First = (Corner[0] - InwardX * Reach, Corner[1] - InwardY * Reach)
    Second = (Corner[0] + OutwardX * Other, Corner[1] + OutwardY * Other)
    Middle: KPlaneSpan = LineSpan(First, Second, Label)
    if Rounded:
        Center = (First[0] - InwardY * AmountCm, First[1] + InwardX * AmountCm)
        Middle = ArcSpan(Center, AmountCm, PointAngle(Center, First), TurnAngle, Label)
    Trimmed = (
        LineSpan(Before.StartCm, First, Before.Label),
        Middle,
        LineSpan(Second, After.FinishCm, After.Label),
    )
    if Index + 1 == len(LoopValue):
        return CanonLoop(Trimmed[1:] + LoopValue[1:Index] + Trimmed[:1])
    return CanonLoop(LoopValue[:Index] + Trimmed + LoopValue[Index + 2 :])
