def ReadMcParts(BlockBody: bytes, Offset: int) -> tuple[int, int, int, int]:
    Value = 0
    Shift = 0
    Position = Offset
    while Position < len(BlockBody):
        ByteValue = BlockBody[Position]
        Position += 1
        if ByteValue < 0x80:
            return Value, Shift, ByteValue, Position
        Value |= (ByteValue & 0x7F) << Shift
        Shift += 7
        if Shift > 63:
            raise ValueError("DWG handle map modular value exceeds 64 bits")
    raise ValueError("DWG handle map modular value is truncated")
