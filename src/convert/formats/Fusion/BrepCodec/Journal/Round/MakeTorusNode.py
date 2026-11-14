from convert.formats.Fusion.BrepCodec.Journal.Round.CheckRoundNode import CheckRoundNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    FloatWord,
    LogicWord,
    PointWord,
    VectorWord,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def MakeTorusNode(Value: TorusNode) -> AsmRecord:
    CheckRoundNode(Value)
    return AsmRecord(
        "torus-surface",
        (
            *MakePrefix(Value.Prefix),
            PointWord(Value.CenterCm),
            VectorWord(Value.AxisVector),
            FloatWord(Value.MajorRadiusCm),
            FloatWord(Value.MinorRadiusCm),
            VectorWord(Value.ReferenceAxis),
            LogicWord(Value.ReversedV),
            *MakeBound(Value.ULower),
            *MakeBound(Value.UUpper),
            *MakeBound(Value.VLower),
            *MakeBound(Value.VUpper),
        ),
    )
