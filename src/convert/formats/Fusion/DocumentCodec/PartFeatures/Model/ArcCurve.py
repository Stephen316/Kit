from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ArcCurve:
    CenterMm: tuple[float, float]
    RadiusMm: float
    StartDegrees: float
    SweepDegrees: float
