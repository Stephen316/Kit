from dataclasses import dataclass as MakeDataClass


# offset specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class OffsetSpec:
    DistanceMm: float
    FeatureName: str = "Offset"
    SideMm: tuple[float, float] | None = None
