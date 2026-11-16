from convert.Formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.Formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    LogicWord,
    RefWord,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the wire node operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeWireNode(Value: WireNode) -> AsmRecord:
    return AsmRecord(
        "wire",
        (
            *MakePrefix(Value.Prefix),
            RefWord(Value.NextWire),
            RefWord(Value.FirstCoedge),
            RefWord(Value.OwnerShell),
            RefWord(-1),
            LogicWord(Value.Inside),
        ),
    )
