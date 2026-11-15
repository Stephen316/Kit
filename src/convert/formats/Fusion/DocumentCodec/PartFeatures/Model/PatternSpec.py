from dataclasses import dataclass as MakeDataClass


# pattern specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class PatternSpec:
    SourceIndex: int
    CountU: int
    SpacingUMm: float
    CountV: int = 1
    SpacingVMm: float = 10.0
    FeatureName: str = "Rectangular Pattern"
