from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ProfileLoop import (
    CurveSpan,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanExtent import (
    SpanExtent,
)

# middle label must remain consistent across callers so feature parameters remain connected to the resulting geometry
KMiddleLabel = FaceLabel("0", ())


# the roof spans contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
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


# the roof middle contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
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
