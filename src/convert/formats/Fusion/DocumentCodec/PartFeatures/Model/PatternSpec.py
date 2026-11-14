from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PatternSpec:
    SourceIndex: int
    CountU: int
    SpacingUMm: float
    CountV: int = 1
    SpacingVMm: float = 10.0
    FeatureName: str = "Rectangular Pattern"
