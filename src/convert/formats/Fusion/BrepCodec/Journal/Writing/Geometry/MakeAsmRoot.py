from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    IntWord,
    RefWord,
    TextWord,
)


def MakeAsmRoot(Value: AsmRoot) -> AsmRecord:
    return AsmRecord(
        "asmheader",
        (
            RefWord(Value.Attribute),
            IntWord(Value.EntityTag),
            TextWord(Value.KernelVersion),
        ),
    )
