from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import RefWord
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix


def MakeShellNode(Value: ShellNode) -> AsmRecord:
    return AsmRecord(
        "shell",
        (
            *MakePrefix(Value.Prefix),
            RefWord(Value.NextShell),
            RefWord(-1),
            RefWord(Value.FirstFace),
            RefWord(Value.FirstWire),
            RefWord(Value.OwnerLump),
        ),
    )
