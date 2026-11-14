from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    FloatWord,
    LogicWord,
    RefWord,
    TextWord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


def MakeEdgeNode(Value: EdgeNode) -> AsmRecord:
    return AsmRecord(
        "edge",
        (
            *MakePrefix(Value.Prefix),
            RefWord(Value.StartVertex),
            FloatWord(Value.StartParam),
            RefWord(Value.EndVertex),
            FloatWord(Value.EndParam),
            RefWord(Value.OwnerCoedge),
            RefWord(Value.CurveRef),
            LogicWord(Value.Reversed),
            TextWord(Value.Convexity),
        ),
    )
