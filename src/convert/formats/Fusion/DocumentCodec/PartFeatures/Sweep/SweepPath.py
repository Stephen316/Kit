from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ProfileLoop import (
    CurveSpan,
    IsJoined,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    ReverseSpan,
    SpanFinish,
    SpanHeading,
    SpanStart,
)

KTurnLimit = 1e-9
KPathLabel = FaceLabel("0", ())
KStartHeading = (0.0, 1.0)


def IsAligned(First: tuple[float, float], Second: tuple[float, float]) -> bool:
    Cross = First[0] * Second[1] - First[1] * Second[0]
    Along = First[0] * Second[0] + First[1] * Second[1]
    return abs(Cross) < KTurnLimit and Along > 0


def IsSameCarrier(First: KPlaneSpan, Second: KPlaneSpan) -> bool:
    if isinstance(First, LineSpan) and isinstance(Second, LineSpan):
        return True
    if isinstance(First, ArcSpan) and isinstance(Second, ArcSpan):
        IsRound = abs(First.RadiusCm - Second.RadiusCm) < KTurnLimit
        return IsRound and IsJoined(First.CenterCm, Second.CenterCm)
    return False


def CheckJoint(Before: KPlaneSpan, After: KPlaneSpan) -> None:
    if not IsAligned(SpanHeading(Before, True), SpanHeading(After, False)):
        raise ValueError("Fusion sweep paths must turn smoothly at every joint")
    if IsSameCarrier(Before, After):
        raise ValueError("Fusion sweep path curves must not continue one another")


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
