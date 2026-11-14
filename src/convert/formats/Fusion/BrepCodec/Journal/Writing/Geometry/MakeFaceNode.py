from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    LogicWord,
    RefWord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeContained import MakeContained


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
