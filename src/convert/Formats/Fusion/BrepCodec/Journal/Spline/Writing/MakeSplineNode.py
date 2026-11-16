from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.MakeRule import MakeScope
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakePrefix import MakePrefix
from convert.Formats.Fusion.BrepCodec.Journal.Writing.WireWords import LogicWord
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the spline node operation needs a consistent construction rule so topology changes retain their native revision relationships
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
