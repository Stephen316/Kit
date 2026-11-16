from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.Formats.Fusion.BrepCodec.Journal.Writing.WireWords import IntWord, RefWord
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


# the vertex node operation needs a consistent construction rule so revision ownership survives native history reconstruction
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
