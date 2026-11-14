from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import RefWord
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


def MakeLumpNode(Value: LumpNode) -> AsmRecord:
    return AsmRecord(
        "lump",
        (
            *MakePrefix(Value.Prefix),
            RefWord(Value.NextLump),
            RefWord(Value.FirstShell),
            RefWord(Value.OwnerBody),
        ),
    )
