from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def MakeSourceLink(Value: SketchLink) -> tuple[KAsmToken, ...]:
    Numbers = (
        Value.PrimaryId,
        Value.SecondaryId,
        Value.Direction,
        Value.TopologyRoleFlags,
        Value.SplitSequenceId,
        Value.SplitTotalNumber,
    )
    return (4, 1), (4, 1), (4, 3), (7, " ".join(str(Number) for Number in Numbers))
