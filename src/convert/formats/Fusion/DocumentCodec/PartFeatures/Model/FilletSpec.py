from dataclasses import dataclass as MakeDataClass


# fillet specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class FilletSpec:
    CornerMm: tuple[float, float]
    RadiusMm: float
    FeatureName: str = "Fillet"
    MoreCornersMm: tuple[tuple[float, float], ...] = ()
    LevelMm: float | None = None
