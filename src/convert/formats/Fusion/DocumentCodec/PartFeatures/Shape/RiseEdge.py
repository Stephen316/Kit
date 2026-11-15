from dataclasses import dataclass as MakeDataClass


# rise edge needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class RiseEdge:
    PointCm: tuple[float, float]
    LowerCm: float
    UpperCm: float
    TopCm: tuple[float, float] | None = None
