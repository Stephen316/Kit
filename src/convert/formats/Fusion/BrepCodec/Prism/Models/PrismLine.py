from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PrismLine:
    OriginCm: tuple[float, float, float]
    DirectionCm: tuple[float, float, float]
    LowerBound: float | None = None
    UpperBound: float | None = None
