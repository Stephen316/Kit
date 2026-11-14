from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class BodyRingSpec:
    SourceBody: int
    Count: int
    TotalDegrees: float = 360.0
    FeatureName: str = "Circular Pattern"
