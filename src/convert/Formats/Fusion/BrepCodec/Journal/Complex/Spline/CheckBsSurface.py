from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
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


# invalid bs surface input must fail here so nested spline and surface records retain their relationships
def CheckBsSurface(Value: BsSurface) -> None:
    if Value.RationalForm not in (("both", "u", "v") if Value.Rational else ("",)):
        raise ValueError("Unsupported Fusion B-spline surface rational form")
    if any(
        type(Singular) is not int or not 0 <= Singular <= 3
        for Singular in (Value.USingular, Value.VSingular)
    ):
        raise ValueError("Unsupported Fusion B-spline surface singularity")
    CheckKnots(Value.UDegree, Value.UClosure, Value.UKnots, Value.UMultiplicity)
    CheckKnots(Value.VDegree, Value.VClosure, Value.VKnots, Value.VMultiplicity)
    Count = PoleCount(Value.UDegree, Value.UMultiplicity) * PoleCount(
        Value.VDegree, Value.VMultiplicity
    )
    CheckPoles(Value.Poles, Count, 3)
    CheckWeights(Value.Rational, Value.Weights, Count)
