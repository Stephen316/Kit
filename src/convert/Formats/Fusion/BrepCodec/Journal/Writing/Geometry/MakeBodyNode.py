from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.Formats.Fusion.BrepCodec.Journal.Writing.WireWords import RefWord
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


# the body node operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeBodyNode(Value: BodyNode) -> AsmRecord:
    return AsmRecord(
        "body",
        (
            *MakePrefix(Value.Prefix),
            RefWord(Value.FirstLump),
            RefWord(-1),
            RefWord(Value.TransformRef),
        ),
    )
