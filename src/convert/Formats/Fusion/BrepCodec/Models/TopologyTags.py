from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


# topology tags needs an explicit state contract so topology identity survives native history reconstruction
@MakeDataClass(frozen=True, slots=True)
class TopologyTags:
    SideFace: FeatureTag
    TopFace: FeatureTag
    BottomFace: FeatureTag
    TopEdge: FeatureTag
    BottomEdge: FeatureTag
    Sketch: SketchLink
