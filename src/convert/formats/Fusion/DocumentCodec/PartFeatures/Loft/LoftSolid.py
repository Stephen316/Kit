from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ProfileLoop import (
    IsJoined,
    ProfileLoop,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    IsFullCircle,
    SpanFinish,
    SpanHeading,
    SpanStart,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ToolSlab import (
    ToolLabels,
    ToolSlab,
)

KParallel = 1e-9


def LoftShaper(Feature: LoftSpec) -> ExtrudeSpec:
    return ExtrudeSpec(Feature.LowerProfile, Feature.HeightMm)


def PairSpan(Lower: KPlaneSpan, Upper: KPlaneSpan) -> KPlaneSpan:
    if isinstance(Lower, LineSpan) and isinstance(Upper, LineSpan):
        First, Second = SpanHeading(Lower, False), SpanHeading(Upper, False)
        Cross = First[0] * Second[1] - First[1] * Second[0]
        Along = First[0] * Second[0] + First[1] * Second[1]
        if abs(Cross) < KParallel and Along > 0:
            return Upper
    if isinstance(Lower, ArcSpan) and isinstance(Upper, ArcSpan):
        Circles = IsFullCircle(Lower) and IsFullCircle(Upper)
        if Circles and IsJoined(Lower.CenterCm, Upper.CenterCm):
            return ReplaceValue(Upper, CenterCm=Lower.CenterCm)
    raise ValueError("Fusion lofts pair parallel lines or coaxial circles")


def LoftRoof(Feature: LoftSpec, Lower: KPlaneLoop, Operation: int) -> KPlaneLoop:
    Labels = ToolLabels(LoftShaper(Feature), Operation)
    Upper = {
        SpanValue.Label: SpanValue
        for SpanValue in ProfileLoop(Feature.UpperProfile, Labels)
    }
    RoofLoop = tuple(PairSpan(SpanValue, Upper[SpanValue.Label]) for SpanValue in Lower)
    for Index, SpanValue in enumerate(RoofLoop):
        if not IsJoined(SpanFinish(RoofLoop[Index - 1]), SpanStart(SpanValue)):
            raise ValueError("Fusion loft profiles must list matching curves in order")
    return RoofLoop


def LoftSolid(Feature: LoftSpec, Operation: int) -> PrismSolid:
    SlabValue = ToolSlab(LoftShaper(Feature), Operation)
    RoofLoop = LoftRoof(Feature, SlabValue.Loops[0], Operation)
    Tapered = ReplaceValue(SlabValue, RoofLoops=(RoofLoop,))
    BodyLabel = FaceLabel(str(Operation), (), len(Feature.LowerProfile) + 3)
    return PrismSolid((Tapered,), BodyLabel)
