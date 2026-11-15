from dataclasses import dataclass as MakeDataClass
from typing import Literal


# plane specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class PlaneSpec:
    OffsetMm: float
    BasePlane: Literal["xy", "yz", "xz"] = "xy"
    FeatureName: str = "Plane"
