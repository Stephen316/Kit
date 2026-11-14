from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan


def CopyLiteralMut(
    Output: bytearray, Packed: bytes, Position: int, Count: int, Limit: int
) -> int:
    if len(Output) + Count > Limit:
        raise ValueError("DWG compressed page exceeds its declared size")
    Output.extend(TakeSpan(Packed, Position, Count, "compressed literal run"))
    return Position + Count
