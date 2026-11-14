from math import isfinite as IsFinite


def CheckWeights(Rational: bool, Weights: tuple[float, ...], Count: int) -> None:
    if type(Weights) is not tuple:
        raise ValueError("Invalid Fusion B-spline rational form")
    if len(Weights) != (Count if Rational else 0):
        raise ValueError("Fusion B-spline weights disagree with its rational form")
    if any(
        type(Value) is not float or not IsFinite(Value) or Value <= 0.0
        for Value in Weights
    ):
        raise ValueError("Fusion B-spline weights must be positive finite doubles")
