from convert.formats.Fusion.DrawingCodec.Dwg.Metadata.ReadWideText import ReadWideText


def ReadTextRun(
    DataValue: bytes, Offset: int, Count: int
) -> tuple[tuple[str, ...], int]:
    if Count * 2 > len(DataValue) - Offset:
        raise ValueError("DWG wide text count exceeds the section data")
    TextValues: list[str] = []
    Position = Offset
    for _ in range(Count):
        TextValue, Position = ReadWideText(DataValue, Position)
        TextValues.append(TextValue)
    return tuple(TextValues), Position
