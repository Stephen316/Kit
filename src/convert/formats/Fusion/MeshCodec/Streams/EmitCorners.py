from struct import pack as PackValue


def EmitCorners(Corners: tuple[int, ...], Terminal: int) -> bytes:
    if type(Terminal) is not int or not -(1 << 31) <= Terminal < 1 << 31:
        raise ValueError("Fusion mesh terminal corner word exceeds int32")
    Deltas = tuple(Second - First for First, Second in zip(Corners, Corners[1:]))
    if any(not -(1 << 31) <= Delta < 1 << 31 for Delta in Deltas):
        raise ValueError("Fusion mesh corner difference exceeds int32")
    return b"".join(PackValue("<i", Value) for Value in (*Deltas, Terminal))
