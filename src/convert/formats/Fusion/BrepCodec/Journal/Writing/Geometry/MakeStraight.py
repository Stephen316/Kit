from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    PointWord,
    VectorWord,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def MakeStraight(Value: StraightNode) -> AsmRecord:
    return AsmRecord(
        "straight-curve",
        (
            *MakePrefix(Value.Prefix),
            PointWord(Value.OriginCm),
            VectorWord(Value.DirectionVector),
            *MakeBound(Value.LowerBound),
            *MakeBound(Value.UpperBound),
        ),
    )
