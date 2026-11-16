from dataclasses import dataclass as MakeDataClass


# arc curve needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class ArcCurve:
    CenterMm: tuple[float, float]
    RadiusMm: float
    StartDegrees: float
    SweepDegrees: float
