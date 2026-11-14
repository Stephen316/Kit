from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class SplineKnot:
    Value: float
    Count: int
