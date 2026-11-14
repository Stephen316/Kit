from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckKnots import (
    CheckKnots,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckPoles import (
    CheckPoles,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckWeights import (
    CheckWeights,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.PoleCount import PoleCount


def CheckBsCurve(Value: BsCurve, Dimension: int) -> None:
    if Value.Dimension != Dimension:
        raise ValueError("Fusion B-spline curve has the wrong dimension")
    CheckKnots(Value.Degree, Value.Closure, Value.Knots, Value.Multiplicity)
    Count = PoleCount(Value.Degree, Value.Multiplicity)
    CheckPoles(Value.Poles, Count, Dimension)
    CheckWeights(Value.Rational, Value.Weights, Count)
