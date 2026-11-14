from math import hypot as Hypotenuse, radians as Radians

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    KProfileCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import LoopArea
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    KFullTurn,
    ReverseSpan,
    SpanFinish,
    SpanStart,
)

KJoinTolerance = 1e-7
KSeamAngle = KFullTurn / 2.0


def CurveSpan(Curve: KProfileCurve, Label: FaceLabel) -> KPlaneSpan:
    if isinstance(Curve, LineCurve):
        Start = (Curve.StartMm[0] / 10.0, Curve.StartMm[1] / 10.0)
        Finish = (Curve.FinishMm[0] / 10.0, Curve.FinishMm[1] / 10.0)
        return LineSpan(Start, Finish, Label)
    Center = (Curve.CenterMm[0] / 10.0, Curve.CenterMm[1] / 10.0)
    if isinstance(Curve, ArcCurve):
        return ArcSpan(
            Center,
            Curve.RadiusMm / 10.0,
            Radians(Curve.StartDegrees),
            Radians(Curve.SweepDegrees),
            Label,
        )
    return ArcSpan(Center, Curve.RadiusMm / 10.0, KSeamAngle, KFullTurn, Label)


def IsJoined(First: tuple[float, float], Second: tuple[float, float]) -> bool:
    return Hypotenuse(First[0] - Second[0], First[1] - Second[1]) < KJoinTolerance


def ChainSpans(Spans: tuple[KPlaneSpan, ...]) -> KPlaneLoop:
    Chain = list(Spans[:1])
    if len(Spans) > 1 and not any(
        IsJoined(SpanFinish(Spans[0]), Point)
        for Point in (SpanStart(Spans[1]), SpanFinish(Spans[1]))
    ):
        Chain = [ReverseSpan(Spans[0])]
    for Value in Spans[1:]:
        IsForward = IsJoined(SpanFinish(Chain[-1]), SpanStart(Value))
        Chain.append(Value if IsForward else ReverseSpan(Value))
        if not IsJoined(SpanFinish(Chain[-2]), SpanStart(Chain[-1])):
            raise ValueError("Fusion part profile curves must form a chain")
    if not IsJoined(SpanFinish(Chain[-1]), SpanStart(Chain[0])):
        raise ValueError("Fusion part profile must be closed")
    return tuple(Chain)


def ReverseLoop(LoopValue: KPlaneLoop) -> KPlaneLoop:
    return CanonLoop(tuple(ReverseSpan(Value) for Value in reversed(LoopValue)))


def ProfileLoop(
    Profile: tuple[KProfileCurve, ...], Labels: tuple[FaceLabel, ...]
) -> KPlaneLoop:
    Spans = tuple(CurveSpan(Curve, Label) for Curve, Label in zip(Profile, Labels))
    LoopValue = CanonLoop(ChainSpans(Spans))
    Enclosed = LoopArea(LoopValue)
    if abs(Enclosed) < 1e-12:
        raise ValueError("Fusion part profile encloses no area")
    return LoopValue if Enclosed > 0 else ReverseLoop(LoopValue)
