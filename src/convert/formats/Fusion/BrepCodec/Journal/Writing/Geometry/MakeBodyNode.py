from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import RefWord
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


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
