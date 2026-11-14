from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class CircularSpec:
    SourceIndex: int
    Count: int
    TotalDegrees: float = 360.0
    FeatureName: str = "Circular Pattern"
