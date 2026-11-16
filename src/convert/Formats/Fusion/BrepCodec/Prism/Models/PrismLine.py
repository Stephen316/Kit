from dataclasses import dataclass as MakeDataClass


# prism line needs an explicit state contract so profile topology remains connected to its extrusion history
@MakeDataClass(frozen=True, slots=True)
class PrismLine:
    OriginCm: tuple[float, float, float]
    DirectionCm: tuple[float, float, float]
    LowerBound: float | None = None
    UpperBound: float | None = None
