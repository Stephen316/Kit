from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# the points operation needs a consistent construction rule so topology changes retain their native revision relationships
def MakePoints(Points: tuple[tuple[float, ...], ...]) -> tuple[KAsmToken, ...]:
    return tuple((6, Number) for Point in Points for Number in Point)
