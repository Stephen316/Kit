from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsCurve import (
    CheckBsCurve,
)


def NegateCurve(Curve: BsCurve) -> BsCurve:
    CheckBsCurve(Curve, Curve.Dimension)
    return BsCurve(
        Curve.Rational,
        Curve.Degree,
        Curve.Closure,
        tuple(-KnotValue for KnotValue in reversed(Curve.Knots)),
        tuple(reversed(Curve.Multiplicity)),
        Curve.Dimension,
        tuple(reversed(Curve.Poles)),
        tuple(reversed(Curve.Weights)),
    )
