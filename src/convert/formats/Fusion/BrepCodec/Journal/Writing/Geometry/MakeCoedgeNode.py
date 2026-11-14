from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    IntWord,
    LogicWord,
    RefWord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


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
