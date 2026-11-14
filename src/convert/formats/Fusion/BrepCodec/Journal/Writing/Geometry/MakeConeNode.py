from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    FloatWord,
    LogicWord,
    PointWord,
    VectorWord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound


def MakeConeNode(Value: ConeNode) -> AsmRecord:
    return AsmRecord(
        "cone-surface",
        (
            *MakePrefix(Value.Prefix),
            PointWord(Value.OriginCm),
            VectorWord(Value.AxisVector),
            VectorWord(Value.MajorAxisCm),
            FloatWord(Value.EllipseRatio),
            *MakeBound(Value.EllipseLower),
            *MakeBound(Value.EllipseUpper),
            FloatWord(Value.SineAngle),
            FloatWord(Value.CosineAngle),
            FloatWord(Value.UScaleCm),
            LogicWord(Value.Reversed),
            *MakeBound(Value.ULower),
            *MakeBound(Value.UUpper),
            *MakeBound(Value.VLower),
            *MakeBound(Value.VUpper),
        ),
    )
