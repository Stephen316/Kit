from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    KProfileCurve,
)


# loft specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class LoftSpec:
    LowerProfile: tuple[KProfileCurve, ...]
    UpperProfile: tuple[KProfileCurve, ...]
    HeightMm: float
    LowerName: str = "Loft base"
    PlaneName: str = "Loft plane"
    UpperName: str = "Loft top"
    FeatureName: str = "Loft"
