from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import RefWord
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


# the loop node operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeLoopNode(Value: LoopNode) -> AsmRecord:
    return AsmRecord(
        "loop",
        (
            *MakePrefix(Value.Prefix),
            RefWord(Value.NextLoop),
            RefWord(Value.FirstCoedge),
            RefWord(Value.OwnerFace),
        ),
    )
