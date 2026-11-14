from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.ReadBackRef import ReadBackRef
from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.ReadLiteral import ReadLiteral
from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.TakeByte import TakeByte
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPackPlan import DwgPackPlan


def ReadPackPlan(Packed: bytes) -> DwgPackPlan:
    Opcode = TakeByte(Packed, 0)
    Position = 1
    LeadCount = 0
    if Opcode < 0x10:
        LeadCount, Position = ReadLiteral(Packed, Position, Opcode)
        Opcode = TakeByte(Packed, Position + LeadCount)
        Position += LeadCount + 1
    PackSteps: list[tuple[int, int, int]] = []
    while Opcode != 0x11:
        Length, Distance, Trailing, Position = ReadBackRef(Packed, Position, Opcode)
        if Trailing == 0:
            Opcode = TakeByte(Packed, Position)
            Position += 1
            if Opcode >= 0x10:
                PackSteps.append((Length, Distance, 0))
                continue
            Trailing, Position = ReadLiteral(Packed, Position, Opcode)
        PackSteps.append((Length, Distance, Trailing))
        Opcode = TakeByte(Packed, Position + Trailing)
        Position += Trailing + 1
    if Packed[Position:] != b"\x00\x00":
        raise ValueError("DWG compressed stream does not end with its marker")
    return DwgPackPlan(LeadCount, tuple(PackSteps))
