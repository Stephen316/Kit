from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    FloatWord,
    PointWord,
    VectorWord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound


def MakeEllipseNode(Value: EllipseNode) -> AsmRecord:
    return AsmRecord(
        "ellipse-curve",
        (
            *MakePrefix(Value.Prefix),
            PointWord(Value.OriginCm),
            VectorWord(Value.Normal),
            VectorWord(Value.MajorAxisCm),
            FloatWord(Value.EllipseRatio),
            *MakeBound(Value.LowerBound),
            *MakeBound(Value.UpperBound),
        ),
    )
