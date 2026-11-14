from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def MakeKnots(
    Knots: tuple[float, ...], Multiplicity: tuple[int, ...]
) -> tuple[KAsmToken, ...]:
    return tuple(
        Token
        for KnotValue, Multiple in zip(Knots, Multiplicity, strict=True)
        for Token in ((6, KnotValue), (4, Multiple))
    )


def MakePoles(
    Poles: tuple[tuple[float, ...], ...], Weights: tuple[float, ...]
) -> tuple[KAsmToken, ...]:
    Tokens: list[KAsmToken] = []
    for Index, Point in enumerate(Poles):
        Tokens.extend((6, Number) for Number in Point)
        if Weights:
            Tokens.append((6, Weights[Index]))
    return tuple(Tokens)
