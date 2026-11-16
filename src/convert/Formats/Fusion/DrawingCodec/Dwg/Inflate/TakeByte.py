# compressed stream reads need explicit bounds so truncated pages cannot become valid drawing data
def TakeByte(Packed: bytes, Position: int) -> int:
    if not 0 <= Position < len(Packed):
        raise ValueError("DWG compressed stream is truncated")
    return Packed[Position]
