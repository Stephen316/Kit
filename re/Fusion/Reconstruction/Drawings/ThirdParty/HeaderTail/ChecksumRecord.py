def TakeBits(DataValue: bytes, BitStart: int, BitCount: int) -> int:
    Value = 0
    for Index in range(BitCount):
        Offset = BitStart + Index
        ByteValue = DataValue[Offset // 8] if Offset // 8 < len(DataValue) else 0
        Value = (Value << 1) | ((ByteValue >> (7 - Offset % 8)) & 1)
    return Value


def HeaderChecksum(DataValue: bytes, EndBit: int) -> int:
    Position = 0
    Total = 0
    while Position < EndBit:
        CodeValue = TakeBits(DataValue, Position, 2)
        Position += 2
        if CodeValue == 0:
            LowValue = TakeBits(DataValue, Position, 8)
            HighValue = TakeBits(DataValue, Position + 8, 8)
            Value = LowValue | (HighValue << 8)
            Position += 16
        elif CodeValue == 1:
            Value = TakeBits(DataValue, Position, 8)
            Position += 8
        elif CodeValue == 2:
            Value = 0
        else:
            Value = 0x100
        if Position <= EndBit:
            Total += Value
    return Total & 0xFFFF
