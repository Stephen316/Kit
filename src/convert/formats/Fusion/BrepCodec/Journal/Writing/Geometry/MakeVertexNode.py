from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import IntWord, RefWord
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


def MakeVertexNode(Value: VertexNode) -> AsmRecord:
    return AsmRecord(
        "vertex",
        (
            *MakePrefix(Value.Prefix),
            RefWord(Value.OwnerEdge),
            IntWord(Value.EdgeIndex),
            RefWord(Value.PointRef),
        ),
    )
