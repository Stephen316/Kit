from dataclasses import dataclass as MakeDataClass


# the value operation needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class UnitValue:
    UnitCode: int
    Magnitude: float
