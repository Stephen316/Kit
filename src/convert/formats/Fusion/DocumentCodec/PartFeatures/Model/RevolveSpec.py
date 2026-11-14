from dataclasses import dataclass as MakeDataClass
from typing import Literal


@MakeDataClass(frozen=True, slots=True)
class RevolveSpec:
    InnerMm: float
    OuterMm: float
    LowerMm: float
    UpperMm: float
    AngleDegrees: float = 360.0
    Operation: Literal["new", "join", "cut"] = "new"
    SketchName: str = "Sketch"
    FeatureName: str = "Revolve"
