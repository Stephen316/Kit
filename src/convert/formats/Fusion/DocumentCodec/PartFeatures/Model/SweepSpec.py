from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)

KPathCurve: TypeAlias = LineCurve | ArcCurve


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
