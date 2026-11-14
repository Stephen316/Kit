from dataclasses import dataclass as MakeDataClass
from typing import Literal


@MakeDataClass(frozen=True, slots=True)
class PlaneSpec:
    OffsetMm: float
    BasePlane: Literal["xy", "yz", "xz"] = "xy"
    FeatureName: str = "Plane"
