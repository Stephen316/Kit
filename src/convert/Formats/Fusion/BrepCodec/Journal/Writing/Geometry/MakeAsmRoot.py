from convert.Formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.Formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    IntWord,
    RefWord,
    TextWord,
)


# the asm root operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeAsmRoot(Value: AsmRoot) -> AsmRecord:
    return AsmRecord(
        "asmheader",
        (
            RefWord(Value.Attribute),
            IntWord(Value.EntityTag),
            TextWord(Value.KernelVersion),
        ),
    )
