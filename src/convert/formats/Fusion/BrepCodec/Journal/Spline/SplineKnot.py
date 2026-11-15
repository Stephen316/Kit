from dataclasses import dataclass as MakeDataClass


# spline knot needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class SplineKnot:
    Value: float
    Count: int
