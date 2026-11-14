from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def MakeBound(Value: float | None) -> tuple[KAsmToken, ...]:
    return ((11, None),) if Value is None else ((10, None), (6, Value))
