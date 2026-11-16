from dataclasses import dataclass as MakeDataClass


# line curve needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class LineCurve:
    StartMm: tuple[float, float]
    FinishMm: tuple[float, float]
