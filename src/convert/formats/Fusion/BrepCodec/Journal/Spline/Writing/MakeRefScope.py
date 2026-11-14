from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef


def MakeRefScope(Value: SubtypeRef, Family: str) -> tuple[KAsmToken, ...]:
    if (
        Value.Family != Family
        or type(Value.Index) is not int
        or not 0 <= Value.Index < (1 << 31)
    ):
        raise ValueError("Fusion subtype reference disagrees with its " + Family)
    return (15, None), (13, "ref"), (4, Value.Index), (16, None)
