from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.TakeByte import TakeByte


def ReadZeroRun(Packed: bytes, Position: int) -> tuple[int, int]:
    Total = 0
    Cursor = Position
    Value = TakeByte(Packed, Cursor)
    while Value == 0:
        Total += 0xFF
        Cursor += 1
        Value = TakeByte(Packed, Cursor)
    return Total + Value, Cursor + 1
