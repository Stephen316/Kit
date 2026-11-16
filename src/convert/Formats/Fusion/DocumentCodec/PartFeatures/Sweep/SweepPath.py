from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ProfileLoop import (
    CurveSpan,
    IsJoined,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    ReverseSpan,
    SpanFinish,
    SpanHeading,
    SpanStart,
)

# the turn limit tolerance prevents rounding noise from creating false geometric distinctions during reconstruction
KTurnLimit = 1e-9

# path label needs a stable location so parametric feature reconstruction resolves inputs independently of the caller working directory
KPathLabel = FaceLabel("0", ())

# the start heading order must stay explicit so feature parameters remain connected to the resulting geometry
KStartHeading = (0.0, 1.0)


# the aligned decision must stay consistent so feature parameters remain connected to the resulting geometry
def IsAligned(First: tuple[float, float], Second: tuple[float, float]) -> bool:
    Cross = First[0] * Second[1] - First[1] * Second[0]
    Along = First[0] * Second[0] + First[1] * Second[1]
    return abs(Cross) < KTurnLimit and Along > 0


# the same carrier decision must stay consistent so feature parameters remain connected to the resulting geometry
def IsSameCarrier(First: KPlaneSpan, Second: KPlaneSpan) -> bool:
    if isinstance(First, LineSpan) and isinstance(Second, LineSpan):
        return True
    if isinstance(First, ArcSpan) and isinstance(Second, ArcSpan):
        IsRound = abs(First.RadiusCm - Second.RadiusCm) < KTurnLimit
        return IsRound and IsJoined(First.CenterCm, Second.CenterCm)
    return False


# invalid joint input must fail here so feature parameters remain connected to the resulting geometry
def CheckJoint(Before: KPlaneSpan, After: KPlaneSpan) -> None:
    if not IsAligned(SpanHeading(Before, True), SpanHeading(After, False)):
        raise ValueError("Fusion sweep paths must turn smoothly at every joint")
    if IsSameCarrier(Before, After):
        raise ValueError("Fusion sweep path curves must not continue one another")


# path spans needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def PathSpans(Feature: SweepSpec) -> KPlaneLoop:
    Chain: list[KPlaneSpan] = []
    Point = (0.0, 0.0)
    for Curve in Feature.Path:
        SpanValue = CurveSpan(Curve, KPathLabel)
        if not IsJoined(SpanStart(SpanValue), Point):
            SpanValue = ReverseSpan(SpanValue)
        if not IsJoined(SpanStart(SpanValue), Point):
            raise ValueError("Fusion sweep paths must chain from the sketch origin")
        if Chain:
            CheckJoint(Chain[-1], SpanValue)
        Chain.append(SpanValue)
        Point = SpanFinish(SpanValue)
    if not IsAligned(SpanHeading(Chain[0], False), KStartHeading):
        raise ValueError("Fusion sweep paths must leave the profile along +Y")
    return tuple(Chain)
