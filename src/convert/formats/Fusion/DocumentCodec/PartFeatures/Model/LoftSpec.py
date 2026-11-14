from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    KProfileCurve,
)


@MakeDataClass(frozen=True, slots=True)
class LoftSpec:
    LowerProfile: tuple[KProfileCurve, ...]
    UpperProfile: tuple[KProfileCurve, ...]
    HeightMm: float
    LowerName: str = "Loft base"
    PlaneName: str = "Loft plane"
    UpperName: str = "Loft top"
    FeatureName: str = "Loft"
