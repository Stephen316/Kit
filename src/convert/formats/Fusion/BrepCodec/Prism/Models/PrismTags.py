from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


@MakeDataClass(frozen=True, slots=True)
class PrismTags:
    Faces: tuple[FeatureTag, ...]
    Sketches: tuple[SketchLink, ...]
