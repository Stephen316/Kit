from dataclasses import dataclass as MakeDataClass


# circular specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class CircularSpec:
    SourceIndex: int
    Count: int
    TotalDegrees: float = 360.0
    FeatureName: str = "Circular Pattern"
