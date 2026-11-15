from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.MakeRule import MakeScope
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import (
    IntcurveNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import LogicWord
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the intcurve operation needs a consistent construction rule so topology changes retain their native revision relationships
def MakeIntcurve(Value: IntcurveNode) -> AsmRecord:
    return AsmRecord(
        "intcurve-curve",
        (
            *MakePrefix(Value.Prefix),
            LogicWord(Value.Reversed),
            *MakeScope("curve", Value.Curve),
            *MakeBound(Value.Lower),
            *MakeBound(Value.Upper),
        ),
    )
