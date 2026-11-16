from math import atan2 as ArcTangent
from math import pi as KHalfTurn
from math import sqrt as SquareRoot

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    Added,
    Cross,
    DotProduct,
    Scaled,
)

# the point triple shape must stay shared so drawing edge authoring uses one contract for compatible values
KPointTriple = tuple[float, float, float]

# full turn must remain consistent across callers so projected boundaries retain their intended visibility and geometry
KFullTurn = 2 * KHalfTurn

# polar limit needs one explicit bound so drawing edge authoring cannot accept inconsistent resource or layout limits
KPolarLimit = 1 / 64

# the world up order must stay explicit so projected boundaries retain their intended visibility and geometry
KWorldUp = (0.0, 1.0, 0.0)

# the world top order must stay explicit so projected boundaries retain their intended visibility and geometry
KWorldTop = (0.0, 0.0, 1.0)


# the minus contract needs a shared interpretation so projected boundaries retain their intended visibility and geometry
def Minus(First: KPointTriple, Second: KPointTriple) -> KPointTriple:
    return (First[0] - Second[0], First[1] - Second[1], First[2] - Second[2])


# the length contract needs a shared interpretation so projected boundaries retain their intended visibility and geometry
def Length(Vector: KPointTriple) -> float:
    return SquareRoot(DotProduct(Vector, Vector))


# the vector operation needs one geometric convention so projected boundaries retain their intended visibility and geometry
def UnitVector(Vector: KPointTriple) -> KPointTriple:
    Magnitude = Length(Vector)
    if Magnitude <= 0:
        raise ValueError("Authored DWG view edge needs a nonzero direction")
    return Scaled(Vector, 1 / Magnitude)


# the combine contract needs a shared interpretation so projected boundaries retain their intended visibility and geometry
def Combine(Origin: KPointTriple, *Parts: tuple[float, KPointTriple]) -> KPointTriple:
    Point = Origin
    for Factor, Vector in Parts:
        Point = Added(Point, Scaled(Vector, Factor))
    return Point


# the arbitrary axis contract needs a shared interpretation so projected boundaries retain their intended visibility and geometry
def ArbitraryAxis(Normal: KPointTriple) -> KPointTriple:
    IsPolar = abs(Normal[0]) < KPolarLimit and abs(Normal[1]) < KPolarLimit
    return UnitVector(Cross(KWorldUp if IsPolar else KWorldTop, Normal))


# the turn angle contract needs a shared interpretation so projected boundaries retain their intended visibility and geometry
def TurnAngle(Vector: KPointTriple, XAxis: KPointTriple, YAxis: KPointTriple) -> float:
    return ArcTangent(DotProduct(Vector, YAxis), DotProduct(Vector, XAxis)) % KFullTurn


# the near decision must stay consistent so projected boundaries retain their intended visibility and geometry
def IsNear(First: KPointTriple, Second: KPointTriple, Tolerance: float) -> bool:
    return Length(Minus(First, Second)) <= Tolerance
