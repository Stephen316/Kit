from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PrismPlane:
    OriginCm: tuple[float, float, float]
    Normal: tuple[float, float, float]
    Basis: tuple[float, float, float]
    ReverseV: bool = False
