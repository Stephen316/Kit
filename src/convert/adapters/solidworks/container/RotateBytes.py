def RotateBytes(DataValue: bytes, ShiftValue: int) -> bytes:
    ShiftValue &= 7
    return bytes(
        ((Value << ShiftValue) | (Value >> (8 - ShiftValue))) & 255
        for Value in DataValue
    )
