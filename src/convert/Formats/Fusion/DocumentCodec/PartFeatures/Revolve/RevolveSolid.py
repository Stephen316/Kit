from math import cos as Cosine, radians as Radians, sin as SineOf

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchPlan,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ExtrudeSolid import (
    ExtrudeSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneLoop
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import KFullTurn

# full angle must remain consistent across callers so feature parameters remain connected to the resulting geometry
KFullAngle = 360.0

# the revolve order order must stay explicit so feature parameters remain connected to the resulting geometry
KRevolveOrder = (2, 1, 0, 3)

# revolve faces must remain consistent across callers so feature parameters remain connected to the resulting geometry
KRevolveFaces = 6

# body secondary must remain consistent across callers so feature parameters remain connected to the resulting geometry
KBodySecondary = 7


# the full turn decision must stay consistent so feature parameters remain connected to the resulting geometry
def IsFullTurn(Feature: RevolveSpec) -> bool:
    return Feature.AngleDegrees == KFullAngle


# the revolve profile contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def RevolveProfile(Feature: RevolveSpec) -> tuple[LineCurve, ...]:
    Inner, Outer = Feature.InnerMm, Feature.OuterMm
    Lower, Upper = 0.0 - Feature.LowerMm, 0.0 - Feature.UpperMm
    return (
        LineCurve((Inner, Lower), (Outer, Lower)),
        LineCurve((Outer, Lower), (Outer, Upper)),
        LineCurve((Outer, Upper), (Inner, Upper)),
        LineCurve((Inner, Upper), (Inner, Lower)),
    )


# the revolve labels contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def RevolveLabels(Operation: int) -> tuple[FaceLabel, ...]:
    return tuple(
        FaceLabel(str(Index + 1), (Operation,)) for Index in range(KRevolveFaces)
    )


# the revolve loops contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
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


# the revolve slab contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def RevolveSlab(Feature: RevolveSpec, Operation: int) -> PrismSlab:
    Labels = RevolveLabels(Operation)
    Loops = RevolveLoops(Feature, Labels)
    Bounds = (Feature.LowerMm / 10.0, Feature.UpperMm / 10.0)
    return PrismSlab(*Bounds, Loops, Labels[4], Labels[2])


# apply revolve needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
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
