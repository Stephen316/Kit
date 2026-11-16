from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    SubtypeNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Conversion.JumpCurve import (
    OrderCurve,
)


# form curve needs an explicit validity boundary so surface geometry retains the control cage shape
def FormCurve(Curve: BsCurve, Jumps: tuple[tuple[float, ...], ...]) -> SubtypeNode:
    if type(Jumps) is not tuple or len(Jumps) != 3:
        raise ValueError("Converted Form edge needs three discontinuity lists")
    return OrderCurve(Curve, Jumps)
