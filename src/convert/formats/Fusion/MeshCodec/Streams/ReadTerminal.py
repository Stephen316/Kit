from struct import iter_unpack as IterUnpack


def ReadTerminal(Payload: bytes) -> tuple[int, ...]:
    if len(Payload) % 4:
        raise ValueError("Misaligned Fusion mesh terminal-delta stream")
    Words = tuple(int(Entry[0]) for Entry in IterUnpack("<I", Payload))
    if not Words:
        return ()
    Deltas = tuple(
        Value if Value < 1 << 31 else Value - (1 << 32) for Value in Words[:-1]
    )
    Current = Words[-1] - sum(Deltas)
    Result = [Current]
    for Delta in Deltas:
        Current += Delta
        Result.append(Current)
    if any(not 0 <= Value < 1 << 32 for Value in Result):
        raise ValueError("Fusion mesh terminal-delta value exceeds uint32")
    return tuple(Result)
