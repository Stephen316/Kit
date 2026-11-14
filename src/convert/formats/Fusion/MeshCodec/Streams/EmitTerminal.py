from struct import pack as PackValue


def EmitTerminal(Values: tuple[int, ...]) -> bytes:
    if any(type(Value) is not int or not 0 <= Value < 1 << 32 for Value in Values):
        raise ValueError("Fusion mesh terminal-delta value exceeds uint32")
    if not Values:
        return b""
    Deltas = tuple(Second - First for First, Second in zip(Values, Values[1:]))
    if any(not -(1 << 31) <= Delta < 1 << 31 for Delta in Deltas):
        raise ValueError("Fusion mesh terminal difference exceeds int32")
    return b"".join(PackValue("<i", Delta) for Delta in Deltas) + PackValue(
        "<I", Values[-1]
    )
