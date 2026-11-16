from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckKnots import (
    CheckKnots,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckPoles import (
    CheckPoles,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckWeights import (
    CheckWeights,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.PoleCount import PoleCount


# invalid bs curve input must fail here so nested spline and surface records retain their relationships
def CheckBsCurve(Value: BsCurve, Dimension: int) -> None:
    if Value.Dimension != Dimension:
        raise ValueError("Fusion B-spline curve has the wrong dimension")
    CheckKnots(Value.Degree, Value.Closure, Value.Knots, Value.Multiplicity)
    Count = PoleCount(Value.Degree, Value.Multiplicity)
    CheckPoles(Value.Poles, Count, Dimension)
    CheckWeights(Value.Rational, Value.Weights, Count)
