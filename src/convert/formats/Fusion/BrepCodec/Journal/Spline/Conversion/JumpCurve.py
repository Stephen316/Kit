from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    ExactCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    ExactIntCur,
)


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


def JumpCurve(Curve: BsCurve, Jumps: tuple[float, ...]) -> SubtypeNode:
    return OrderCurve(Curve, ((), (), tuple(Jumps)))
