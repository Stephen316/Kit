from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.MakeRule import MakeScope
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    FloatWord,
    IntWord,
    LogicWord,
    RefWord,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, KAsmToken


def MakePcurveNode(Value: PcurveNode) -> AsmRecord:
    Payload: tuple[KAsmToken, ...]
    if Value.Form == 0 and Value.Curve is not None and Value.CurveRef == -1:
        Payload = (LogicWord(Value.Reversed), *MakeScope("pcurve", Value.Curve))
    elif Value.Form in (-2, -1, 1, 2) and Value.Curve is None and not Value.Reversed:
        Payload = (RefWord(Value.CurveRef),)
    else:
        raise ValueError("Fusion pcurve form disagrees with its carrier")
    return AsmRecord(
        "pcurve",
        (
            *MakePrefix(Value.Prefix),
            IntWord(Value.Form),
            *Payload,
            FloatWord(Value.OffsetU),
            FloatWord(Value.OffsetV),
        ),
    )
