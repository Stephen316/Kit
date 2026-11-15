from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.ReadZeroRun import ReadZeroRun


# compressed pages need unambiguous literal lengths so short and extended runs decode consistently
def ReadLiteral(Packed: bytes, Position: int, Opcode: int) -> tuple[int, int]:
    if Opcode != 0:
        return Opcode + 3, Position
    RunTotal, Cursor = ReadZeroRun(Packed, Position)
    return RunTotal + 0x12, Cursor
