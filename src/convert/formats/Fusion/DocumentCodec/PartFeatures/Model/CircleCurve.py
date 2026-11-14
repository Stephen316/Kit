from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class CircleCurve:
    CenterMm: tuple[float, float]
    RadiusMm: float
