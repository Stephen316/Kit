from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ChamferSpec:
    CornerMm: tuple[float, float]
    DistanceMm: float
    FeatureName: str = "Chamfer"
    SecondMm: float = 0.0
    AngleDegrees: float = 0.0
    MoreCornersMm: tuple[tuple[float, float], ...] = ()
    LevelMm: float | None = None
