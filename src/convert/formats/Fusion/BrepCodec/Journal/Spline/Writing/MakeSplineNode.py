from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.MakeRule import MakeScope
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import LogicWord
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def MakeSplineNode(Value: SplineNode) -> AsmRecord:
    return AsmRecord(
        "spline-surface",
        (
            *MakePrefix(Value.Prefix),
            LogicWord(Value.Reversed),
            *MakeScope("surface", Value.Surface),
            *MakeBound(Value.ULower),
            *MakeBound(Value.UUpper),
            *MakeBound(Value.VLower),
            *MakeBound(Value.VUpper),
        ),
    )
