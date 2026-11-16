from dataclasses import dataclass as MakeDataClass
from typing import Literal


# combine specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class CombineSpec:
    TargetBody: int = 1
    ToolBodies: tuple[int, ...] = (2,)
    Operation: Literal["join", "cut", "intersect"] = "join"
    KeepTools: bool = False
    FeatureName: str = "Combine"
