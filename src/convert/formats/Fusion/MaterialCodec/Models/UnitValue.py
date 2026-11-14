from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class UnitValue:
    UnitCode: int
    Magnitude: float
