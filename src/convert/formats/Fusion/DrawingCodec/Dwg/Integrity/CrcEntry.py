def CrcEntry(Index: int) -> int:
    Value = Index
    for _ in range(8):
        Value = Value >> 1 ^ (0xA001 if Value & 1 else 0)
    return Value
