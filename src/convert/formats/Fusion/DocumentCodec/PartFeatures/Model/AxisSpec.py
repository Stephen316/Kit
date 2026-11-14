from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class AxisSpec:
    CornerMm: tuple[float, float]
    FeatureName: str = "Axis"
