from math import isfinite as IsFinite


def CheckPoles(Poles: tuple[tuple[float, ...], ...], Count: int, Width: int) -> None:
    if type(Poles) is not tuple or len(Poles) != Count:
        raise ValueError("Fusion B-spline pole count disagrees with its knots")
    for Point in Poles:
        if type(Point) is not tuple or len(Point) != Width:
            raise ValueError("Fusion B-spline pole has the wrong dimension")
        if any(type(Value) is not float or not IsFinite(Value) for Value in Point):
            raise ValueError("Fusion B-spline poles must be finite doubles")
