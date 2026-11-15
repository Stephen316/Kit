from dataclasses import dataclass as MakeDataClass


# the value operation needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class VectorValue:
    XCoord: float
    YCoord: float
    ZCoord: float
