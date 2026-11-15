from dataclasses import dataclass as MakeDataClass


# bs surface needs an explicit state contract so nested spline and surface records retain their relationships
@MakeDataClass(frozen=True, slots=True)
class BsSurface:
    Rational: bool
    RationalForm: str
    UDegree: int
    VDegree: int
    UClosure: int
    VClosure: int
    USingular: int
    VSingular: int
    UKnots: tuple[float, ...]
    UMultiplicity: tuple[int, ...]
    VKnots: tuple[float, ...]
    VMultiplicity: tuple[int, ...]
    Poles: tuple[tuple[float, ...], ...]
    Weights: tuple[float, ...]
