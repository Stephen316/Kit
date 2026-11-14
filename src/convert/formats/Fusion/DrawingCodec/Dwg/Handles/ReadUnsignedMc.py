from convert.formats.Fusion.DrawingCodec.Dwg.Handles.ReadMcParts import ReadMcParts


def ReadUnsignedMc(BlockBody: bytes, Offset: int) -> tuple[int, int]:
    Value, Shift, FinalByte, Position = ReadMcParts(BlockBody, Offset)
    return Value | FinalByte << Shift, Position
