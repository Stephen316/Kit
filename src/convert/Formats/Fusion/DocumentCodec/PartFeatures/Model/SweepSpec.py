from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)

# the path curve variants need one shared contract so parametric feature reconstruction cannot omit a supported value shape
KPathCurve: TypeAlias = LineCurve | ArcCurve


# sweep specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class SweepSpec:
    Path: tuple[KPathCurve, ...]
    LeftMm: float
    RightMm: float
    LowerMm: float
    UpperMm: float
    ProfileName: str = "Sweep profile"
    PathName: str = "Sweep path"
    FeatureName: str = "Sweep"
