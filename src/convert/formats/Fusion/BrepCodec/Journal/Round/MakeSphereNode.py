from convert.formats.Fusion.BrepCodec.Journal.Round.CheckRoundNode import CheckRoundNode
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    FloatWord,
    LogicWord,
    PointWord,
    VectorWord,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def MakeSphereNode(Value: SphereNode) -> AsmRecord:
    CheckRoundNode(Value)
    return AsmRecord(
        "sphere-surface",
        (
            *MakePrefix(Value.Prefix),
            PointWord(Value.CenterCm),
            FloatWord(Value.RadiusCm),
            VectorWord(Value.ReferenceAxis),
            VectorWord(Value.PoleDirection),
            LogicWord(Value.ReversedV),
            *MakeBound(Value.ULower),
            *MakeBound(Value.UUpper),
            *MakeBound(Value.VLower),
            *MakeBound(Value.VUpper),
        ),
    )
