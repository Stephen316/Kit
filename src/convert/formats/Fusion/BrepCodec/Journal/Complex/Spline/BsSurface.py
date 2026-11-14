from dataclasses import dataclass as MakeDataClass


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
