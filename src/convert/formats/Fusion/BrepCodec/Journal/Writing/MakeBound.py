from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# the bound operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeBound(Value: float | None) -> tuple[KAsmToken, ...]:
    return ((11, None),) if Value is None else ((10, None), (6, Value))
