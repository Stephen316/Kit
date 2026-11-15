from dataclasses import dataclass as MakeDataClass


# draft specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class DraftSpec:
    AngleDegrees: float
    FeatureName: str = "Draft"
