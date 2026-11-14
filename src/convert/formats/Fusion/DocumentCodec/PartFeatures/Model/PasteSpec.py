from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PasteSpec:
    SourceBody: int = 1
    FeatureName: str = "Paste"
