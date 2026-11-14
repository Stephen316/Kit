from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.ReadExtended import ReadExtended
from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.TakeByte import TakeByte


def ReadBackRef(Packed: bytes, Position: int, Opcode: int) -> tuple[int, int, int, int]:
    Cursor = Position
    if Opcode >= 0x40:
        Second = TakeByte(Packed, Cursor)
        Distance = Second << 2 | (Opcode & 0x0C) >> 2
        return (Opcode >> 4) - 1, Distance, Opcode & 3, Cursor + 1
    if Opcode >= 0x21:
        Length, OffsetBias = Opcode - 0x1E, 0
    elif Opcode == 0x20:
        Extra, Cursor = ReadExtended(Packed, Cursor)
        Length, OffsetBias = Extra + 0x21, 0
    elif Opcode >= 0x12:
        Length, OffsetBias = (Opcode & 0x0F) + 2, 0x3FFF
    elif Opcode == 0x10:
        Extra, Cursor = ReadExtended(Packed, Cursor)
        Length, OffsetBias = Extra + 9, 0x3FFF
    else:
        raise ValueError(f"DWG compressed stream has invalid opcode {Opcode:#x}")
    First = TakeByte(Packed, Cursor)
    Second = TakeByte(Packed, Cursor + 1)
    Distance = (First >> 2 | Second << 6) + OffsetBias
    return Length, Distance, First & 3, Cursor + 2
