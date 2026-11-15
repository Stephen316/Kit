from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# the contained operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeContained(DoubleSided: bool, Contained: bool | None) -> tuple[KAsmToken, ...]:
    if not DoubleSided:
        if Contained is not None:
            raise ValueError("Single-sided Fusion face cannot have containment")
        return ()
    if type(Contained) is not bool:
        raise ValueError("Double-sided Fusion face requires containment")
    return (((10 if Contained else 11), None),)
