from convert.Formats.Fusion.DrawingCodec.Dwg.Handles.ReadMcParts import ReadMcParts


# the unsigned mc operation needs a distinct decoding boundary so object references resolve within the declared object stream
def ReadUnsignedMc(BlockBody: bytes, Offset: int) -> tuple[int, int]:
    Value, Shift, FinalByte, Position = ReadMcParts(BlockBody, Offset)
    return Value | FinalByte << Shift, Position
