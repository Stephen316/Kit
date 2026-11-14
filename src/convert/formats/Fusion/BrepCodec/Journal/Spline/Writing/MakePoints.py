from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def MakePoints(Points: tuple[tuple[float, ...], ...]) -> tuple[KAsmToken, ...]:
    return tuple((6, Number) for Point in Points for Number in Point)
