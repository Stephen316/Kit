from dataclasses import dataclass as MakeDataClass


# circle curve needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class CircleCurve:
    CenterMm: tuple[float, float]
    RadiusMm: float
