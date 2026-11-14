from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def MakeJumps(Jumps: tuple[tuple[float, ...], ...]) -> tuple[KAsmToken, ...]:
    return tuple(
        Field
        for Values in Jumps
        for Field in ((4, len(Values)), *((6, Number) for Number in Values))
    )
