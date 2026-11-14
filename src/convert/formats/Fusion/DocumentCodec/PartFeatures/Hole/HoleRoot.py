from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ProfileLoop import (
    CurveSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanExtent import (
    SpanExtent,
)

KMiddleLabel = FaceLabel("0", ())


def RoofSpans(
    Stages: tuple[PartStage, ...], Stage: PartStage
) -> tuple[KPlaneSpan, ...]:
    Ceiling = Stage.Before.Slabs[-1]
    Creators = Ceiling.RoofLabel.OperationIds[:1]
    for Value in Stages:
        Feature = Value.Feature
        if isinstance(Feature, ExtrudeSpec) and set(Creators) & set(Value.Operations):
            return tuple(CurveSpan(Curve, KMiddleLabel) for Curve in Feature.Profile)
    return tuple(SpanValue for LoopValue in Ceiling.Loops for SpanValue in LoopValue)


def RoofMiddle(Stages: tuple[PartStage, ...], Stage: PartStage) -> tuple[float, float]:
    Points = [
        Point for Value in RoofSpans(Stages, Stage) for Point in SpanExtent(Value)
    ]
    Across = [Point[0] for Point in Points]
    Along = [Point[1] for Point in Points]
    return (
        (min(Across) + max(Across)) / 2.0,
        (min(Along) + max(Along)) / 2.0,
    )
