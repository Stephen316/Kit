from math import cos as Cosine, radians as Radians, sin as SineOf

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchPlan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ExtrudeSolid import (
    ExtrudeSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import KFullTurn

KFullAngle = 360.0
KRevolveOrder = (2, 1, 0, 3)
KRevolveFaces = 6
KBodySecondary = 7


def IsFullTurn(Feature: RevolveSpec) -> bool:
    return Feature.AngleDegrees == KFullAngle


def RevolveProfile(Feature: RevolveSpec) -> tuple[LineCurve, ...]:
    Inner, Outer = Feature.InnerMm, Feature.OuterMm
    Lower, Upper = 0.0 - Feature.LowerMm, 0.0 - Feature.UpperMm
    return (
        LineCurve((Inner, Lower), (Outer, Lower)),
        LineCurve((Outer, Lower), (Outer, Upper)),
        LineCurve((Outer, Upper), (Inner, Upper)),
        LineCurve((Inner, Upper), (Inner, Lower)),
    )


def RevolveLabels(Operation: int) -> tuple[FaceLabel, ...]:
    return tuple(
        FaceLabel(str(Index + 1), (Operation,)) for Index in range(KRevolveFaces)
    )


def RevolveLoops(
    Feature: RevolveSpec, Labels: tuple[FaceLabel, ...]
) -> tuple[KPlaneLoop, ...]:
    Inner, Outer = Feature.InnerMm / 10.0, Feature.OuterMm / 10.0
    Center = (0.0, 0.0)
    if IsFullTurn(Feature):
        return (
            (ArcSpan(Center, Outer, 0.0, KFullTurn, Labels[3]),),
            (ArcSpan(Center, Inner, 0.0, -KFullTurn, Labels[5]),),
        )
    Sweep = Radians(Feature.AngleDegrees)
    TurnX, TurnY = Cosine(Sweep), SineOf(Sweep)
    Spans = (
        LineSpan((Inner, 0.0), (Outer, 0.0), Labels[0]),
        ArcSpan(Center, Outer, 0.0, Sweep, Labels[3]),
        LineSpan(
            (Outer * TurnX, Outer * TurnY), (Inner * TurnX, Inner * TurnY), Labels[1]
        ),
        ArcSpan(Center, Inner, Sweep, -Sweep, Labels[5]),
    )
    return (CanonLoop(Spans),)


def RevolveSlab(Feature: RevolveSpec, Operation: int) -> PrismSlab:
    Labels = RevolveLabels(Operation)
    Loops = RevolveLoops(Feature, Labels)
    Bounds = (Feature.LowerMm / 10.0, Feature.UpperMm / 10.0)
    return PrismSlab(*Bounds, Loops, Labels[4], Labels[2])


def ApplyRevolve(
    Solid: PrismSolid | None, Feature: RevolveSpec, Operation: int, Sketched: SketchPlan
) -> PrismSolid:
    if len(Sketched.Edges) != len(KRevolveOrder):
        raise ValueError("Fusion revolves require a four line profile")
    Shaper = RevolveSlab(Feature, Operation + 1)
    BodyLabel = FaceLabel(str(Operation + 1), (), KBodySecondary)
    if Feature.Operation == "new":
        return PrismSolid((Shaper,), BodyLabel)
    if Solid is None:
        raise ValueError("Fusion part revolve requires an existing body")
    Joined = BodyLabel if Feature.Operation == "join" else None
    return ExtrudeSolid(Solid, Shaper, Feature.Operation, Joined)
