from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.Formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    LogicWord,
    RefWord,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeContained import MakeContained


# the face node operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeFaceNode(Value: FaceNode) -> AsmRecord:
    return AsmRecord(
        "face",
        (
            *MakePrefix(Value.Prefix),
            RefWord(Value.NextFace),
            RefWord(Value.FirstLoop),
            RefWord(Value.OwnerShell),
            RefWord(-1),
            RefWord(Value.Surface),
            LogicWord(Value.Reversed),
            LogicWord(Value.DoubleSided),
            *MakeContained(Value.DoubleSided, Value.Contained),
        ),
    )
