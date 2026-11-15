from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


# prism tags needs an explicit state contract so profile topology remains connected to its extrusion history
@MakeDataClass(frozen=True, slots=True)
class PrismTags:
    Faces: tuple[FeatureTag, ...]
    Sketches: tuple[SketchLink, ...]
