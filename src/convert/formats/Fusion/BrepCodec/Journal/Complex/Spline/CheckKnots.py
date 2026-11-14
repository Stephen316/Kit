from math import isfinite as IsFinite


def CheckKnots(
    Degree: int, Closure: int, Knots: tuple[float, ...], Multiplicity: tuple[int, ...]
) -> None:
    if type(Degree) is not int or not 1 <= Degree <= 25 or Closure not in (0, 1, 2):
        raise ValueError("Unsupported Fusion B-spline degree or closure")
    if (
        type(Knots) is not tuple
        or type(Multiplicity) is not tuple
        or not 2 <= len(Knots) == len(Multiplicity) <= 4096
    ):
        raise ValueError("Invalid Fusion B-spline knot table")
    if any(type(Value) is not float or not IsFinite(Value) for Value in Knots):
        raise ValueError("Fusion B-spline knots must be finite doubles")
    if any(Lower >= Upper for Lower, Upper in zip(Knots, Knots[1:])):
        raise ValueError("Fusion B-spline knots must strictly increase")
    if any(
        type(Value) is not int or not 1 <= Value <= Degree + 1 for Value in Multiplicity
    ):
        raise ValueError("Invalid Fusion B-spline knot multiplicity")
    if sum(Multiplicity) - Degree + 1 < 2:
        raise ValueError("Fusion B-spline requires at least two poles")
