from math import atan2 as ArcTangent
from math import pi as KHalfTurn
from math import sqrt as SquareRoot

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    Added,
    Cross,
    DotProduct,
    Scaled,
)

KPointTriple = tuple[float, float, float]
KFullTurn = 2 * KHalfTurn
KPolarLimit = 1 / 64
KWorldUp = (0.0, 1.0, 0.0)
KWorldTop = (0.0, 0.0, 1.0)


def Minus(First: KPointTriple, Second: KPointTriple) -> KPointTriple:
    return (First[0] - Second[0], First[1] - Second[1], First[2] - Second[2])


def Length(Vector: KPointTriple) -> float:
    return SquareRoot(DotProduct(Vector, Vector))


def UnitVector(Vector: KPointTriple) -> KPointTriple:
    Magnitude = Length(Vector)
    if Magnitude <= 0:
        raise ValueError("Authored DWG view edge needs a nonzero direction")
    return Scaled(Vector, 1 / Magnitude)


def Combine(Origin: KPointTriple, *Parts: tuple[float, KPointTriple]) -> KPointTriple:
    Point = Origin
    for Factor, Vector in Parts:
        Point = Added(Point, Scaled(Vector, Factor))
    return Point


def ArbitraryAxis(Normal: KPointTriple) -> KPointTriple:
    IsPolar = abs(Normal[0]) < KPolarLimit and abs(Normal[1]) < KPolarLimit
    return UnitVector(Cross(KWorldUp if IsPolar else KWorldTop, Normal))


def TurnAngle(Vector: KPointTriple, XAxis: KPointTriple, YAxis: KPointTriple) -> float:
    return ArcTangent(DotProduct(Vector, YAxis), DotProduct(Vector, XAxis)) % KFullTurn


def IsNear(First: KPointTriple, Second: KPointTriple, Tolerance: float) -> bool:
    return Length(Minus(First, Second)) <= Tolerance
