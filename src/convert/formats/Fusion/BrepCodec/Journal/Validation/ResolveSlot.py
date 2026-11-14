def ResolveSlot(Aliases: tuple[int, ...], Reference: int) -> int:
    Visited: set[int] = set()
    while Aliases[Reference] != Reference:
        if Reference in Visited:
            raise ValueError("Cyclic Fusion revision aliases")
        Visited.add(Reference)
        Reference = Aliases[Reference]
    return Reference
