from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.Formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    IntWord,
    LogicWord,
    RefWord,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


# the coedge node operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeCoedgeNode(Value: CoedgeNode) -> AsmRecord:
    return AsmRecord(
        "coedge",
        (
            *MakePrefix(Value.Prefix),
            RefWord(Value.NextCoedge),
            RefWord(Value.PriorCoedge),
            RefWord(Value.Partner),
            RefWord(Value.EdgeRef),
            LogicWord(Value.Reversed),
            RefWord(Value.OwnerLoop),
            IntWord(0),
            RefWord(Value.Pcurve),
        ),
    )
