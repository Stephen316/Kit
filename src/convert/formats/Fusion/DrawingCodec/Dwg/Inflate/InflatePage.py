from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.CopyLiteralMut import (
    CopyLiteralMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.CopyMatchMut import CopyMatchMut
from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.ReadBackRef import ReadBackRef
from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.ReadLiteral import ReadLiteral
from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.TakeByte import TakeByte


def InflatePage(Packed: bytes, Limit: int) -> bytes:
    Output = bytearray()
    Opcode = TakeByte(Packed, 0)
    Position = 1
    if Opcode < 0x10:
        Count, Position = ReadLiteral(Packed, Position, Opcode)
        Position = CopyLiteralMut(Output, Packed, Position, Count, Limit)
        Opcode = TakeByte(Packed, Position)
        Position += 1
    while Opcode != 0x11:
        Length, Distance, Trailing, Position = ReadBackRef(Packed, Position, Opcode)
        CopyMatchMut(Output, Distance, Length, Limit)
        if Trailing == 0:
            Opcode = TakeByte(Packed, Position)
            Position += 1
            if Opcode >= 0x10:
                continue
            Trailing, Position = ReadLiteral(Packed, Position, Opcode)
        Position = CopyLiteralMut(Output, Packed, Position, Trailing, Limit)
        Opcode = TakeByte(Packed, Position)
        Position += 1
    return bytes(Output)
