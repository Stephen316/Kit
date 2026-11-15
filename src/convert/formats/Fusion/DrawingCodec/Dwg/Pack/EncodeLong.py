# the run operation needs a consistent construction rule so section boundaries and object references remain consistent
def EncodeRun(Value: int) -> bytes:
    if Value < 1:
        raise ValueError("DWG compressed run length must be positive")
    ZeroCount = (Value - 1) // 0xFF
    return bytes(ZeroCount) + bytes((Value - ZeroCount * 0xFF,))


# the long operation needs a consistent construction rule so section boundaries and object references remain consistent
def EncodeLong(Value: int) -> bytes:
    if 0 < Value <= 0xFF:
        return bytes((Value,))
    return b"\x00" + EncodeRun(Value - 0xFF)


# the count operation needs a consistent construction rule so section boundaries and object references remain consistent
def EncodeCount(Count: int) -> bytes:
    if Count < 4:
        raise ValueError("DWG literal run shorter than four bytes needs a match")
    if Count <= 0x12:
        return bytes((Count - 3,))
    return b"\x00" + EncodeRun(Count - 0x12)
