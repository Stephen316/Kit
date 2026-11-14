from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RiseEdge:
    PointCm: tuple[float, float]
    LowerCm: float
    UpperCm: float
    TopCm: tuple[float, float] | None = None
