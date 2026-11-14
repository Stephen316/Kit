from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class VectorValue:
    XCoord: float
    YCoord: float
    ZCoord: float
