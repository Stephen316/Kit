from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class FilletSpec:
    CornerMm: tuple[float, float]
    RadiusMm: float
    FeatureName: str = "Fillet"
    MoreCornersMm: tuple[tuple[float, float], ...] = ()
    LevelMm: float | None = None
