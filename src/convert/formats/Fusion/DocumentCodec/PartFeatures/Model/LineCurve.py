from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class LineCurve:
    StartMm: tuple[float, float]
    FinishMm: tuple[float, float]
