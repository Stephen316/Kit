from dataclasses import dataclass as MakeDataClass


# bs curve needs an explicit state contract so nested spline and surface records retain their relationships
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
