def FlipDirection(Direction: int) -> int:
    if Direction == (1 << 32) - 1:
        return Direction
    if Direction not in (0, 1):
        raise ValueError("Unsupported Fusion BRep sketch direction")
    return 1 - Direction
