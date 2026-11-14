from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class BsCurve:
    Rational: bool
    Degree: int
    Closure: int
    Knots: tuple[float, ...]
    Multiplicity: tuple[int, ...]
    Dimension: int
    Poles: tuple[tuple[float, ...], ...]
    Weights: tuple[float, ...]
