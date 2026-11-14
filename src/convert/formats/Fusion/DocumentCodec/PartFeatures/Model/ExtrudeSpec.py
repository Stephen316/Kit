from dataclasses import dataclass as MakeDataClass
from typing import Literal, TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)

KProfileCurve: TypeAlias = LineCurve | ArcCurve | CircleCurve


@MakeDataClass(frozen=True, slots=True)
class ExtrudeSpec:
    Profile: tuple[KProfileCurve, ...]
    DistanceMm: float
    Operation: Literal["new", "join", "cut", "intersect"] = "new"
    Extent: Literal["one", "flip", "symmetric", "two"] = "one"
    AgainstMm: float = 0.0
    SketchName: str = "Sketch"
    FeatureName: str = "Extrude"
