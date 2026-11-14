from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DraftSpec:
    AngleDegrees: float
    FeatureName: str = "Draft"
