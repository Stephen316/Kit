from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PointSpec:
    CornerMm: tuple[float, float]
    FeatureName: str = "Point"
