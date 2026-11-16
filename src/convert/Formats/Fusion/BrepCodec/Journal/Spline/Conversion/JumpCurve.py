from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    ExactCurve,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    SubtypeNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    ExactIntCur,
)


# the order curve contract needs a stable decomposition so surface geometry retains the control cage shape
def OrderCurve(Curve: BsCurve, Lists: tuple[tuple[float, ...], ...]) -> SubtypeNode:
    if type(Lists) is not tuple or len(Lists) != 3:
        raise ValueError("Fusion exact curve needs three discontinuity lists")
    Plain = ExactCurve(Curve)
    Record = Plain.Body
    if not isinstance(Record, ExactIntCur):
        raise ValueError("Fusion exact curve has an unexpected body")
    Breaks = (
        tuple(float(Value) for Value in Lists[0]),
        tuple(float(Value) for Value in Lists[1]),
        tuple(float(Value) for Value in Lists[2]),
    )
    Context = ReplaceValue(Record.Context, Discontinuities=Breaks)
    return SubtypeNode(Plain.SubtypeName, ReplaceValue(Record, Context=Context))


# the jump curve contract needs a shared interpretation so surface geometry retains the control cage shape
def JumpCurve(Curve: BsCurve, Jumps: tuple[float, ...]) -> SubtypeNode:
    return OrderCurve(Curve, ((), (), tuple(Jumps)))
