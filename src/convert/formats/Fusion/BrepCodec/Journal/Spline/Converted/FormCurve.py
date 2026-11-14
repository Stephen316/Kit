from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.JumpCurve import (
    OrderCurve,
)


def FormCurve(Curve: BsCurve, Jumps: tuple[tuple[float, ...], ...]) -> SubtypeNode:
    if type(Jumps) is not tuple or len(Jumps) != 3:
        raise ValueError("Converted Form edge needs three discontinuity lists")
    return OrderCurve(Curve, Jumps)
