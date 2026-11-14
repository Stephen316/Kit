from convert.formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    LogicWord,
    RefWord,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


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
