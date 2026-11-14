from struct import iter_unpack as IterUnpack


def ReadCorners(Payload: bytes, Vertices: int) -> tuple[tuple[int, ...], int]:
    if not Payload or len(Payload) % 12:
        raise ValueError("Invalid Fusion mesh triangle corner allocation")
    Words = tuple(int(Entry[0]) for Entry in IterUnpack("<i", Payload))
    Current = 0
    Relative = [Current]
    for Delta in Words[:-1]:
        Current += Delta
        Relative.append(Current)
    Initial = -min(Relative)
    if Initial != Vertices - 1 - max(Relative):
        raise ValueError(
            "Fusion mesh corner range does not identify its initial vertex"
        )
    return tuple(Value + Initial for Value in Relative), Words[-1]
