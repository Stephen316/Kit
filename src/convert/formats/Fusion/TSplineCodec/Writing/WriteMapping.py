from convert.formats.Fusion.TSplineCodec.Model.GripMapping import GripMapping


def WriteMapping(Mapping: GripMapping | None) -> tuple[str, ...]:
    if Mapping is None:
        return ()
    Owners = tuple(
        ("0m gvp " if Value.IsPrimary else "0m gv ") + str(Value.VertexIndex)
        for Value in Mapping.Owners
    )
    Compounds = tuple(
        "0m cg "
        + " ".join(
            map(
                str,
                (
                    Value.VertexIndex,
                    len(Value.SpokeLengths),
                    *Value.SpokeLengths,
                    *Value.GripIndices,
                ),
            )
        )
        for Value in Mapping.Compounds
    )
    return ("0m odd-grip-map",) + Owners + Compounds
