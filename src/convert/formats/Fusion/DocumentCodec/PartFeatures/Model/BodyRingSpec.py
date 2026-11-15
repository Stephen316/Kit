from dataclasses import dataclass as MakeDataClass


# body ring specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class BodyRingSpec:
    SourceBody: int
    Count: int
    TotalDegrees: float = 360.0
    FeatureName: str = "Circular Pattern"
