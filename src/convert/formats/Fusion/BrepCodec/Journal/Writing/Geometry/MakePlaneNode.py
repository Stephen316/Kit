from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    LogicWord,
    PointWord,
    VectorWord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound


def MakePlaneNode(Value: PlaneNode) -> AsmRecord:
    return AsmRecord(
        "plane-surface",
        (
            *MakePrefix(Value.Prefix),
            PointWord(Value.OriginCm),
            VectorWord(Value.Normal),
            VectorWord(Value.ReferenceAxis),
            LogicWord(Value.ReversedV),
            *MakeBound(Value.ULower),
            *MakeBound(Value.UUpper),
            *MakeBound(Value.VLower),
            *MakeBound(Value.VUpper),
        ),
    )
