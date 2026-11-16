from convert.Formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.Formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    PointWord,
    VectorWord,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the straight operation needs a consistent construction rule so revision ownership survives native history reconstruction
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
