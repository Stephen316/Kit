from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# the jumps operation needs a consistent construction rule so topology changes retain their native revision relationships
def MakeJumps(Jumps: tuple[tuple[float, ...], ...]) -> tuple[KAsmToken, ...]:
    return tuple(
        Field
        for Values in Jumps
        for Field in ((4, len(Values)), *((6, Number) for Number in Values))
    )
