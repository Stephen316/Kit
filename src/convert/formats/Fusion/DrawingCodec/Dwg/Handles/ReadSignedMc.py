from convert.formats.Fusion.DrawingCodec.Dwg.Handles.ReadMcParts import ReadMcParts


def ReadSignedMc(BlockBody: bytes, Offset: int) -> tuple[int, int]:
    Value, Shift, FinalByte, Position = ReadMcParts(BlockBody, Offset)
    Magnitude = Value | (FinalByte & 0x3F) << Shift
    return (-Magnitude if FinalByte & 0x40 else Magnitude), Position
