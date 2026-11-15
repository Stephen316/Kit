from dataclasses import dataclass as MakeDataClass


# paste specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class PasteSpec:
    SourceBody: int = 1
    FeatureName: str = "Paste"
