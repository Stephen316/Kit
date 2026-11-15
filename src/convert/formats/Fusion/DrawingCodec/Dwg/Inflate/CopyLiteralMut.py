from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan


# copy literal needs an explicit validity boundary so compressed page boundaries cannot overrun their declared payload
def CopyLiteralMut(
    Output: bytearray, Packed: bytes, Position: int, Count: int, Limit: int
) -> int:
    if len(Output) + Count > Limit:
        raise ValueError("DWG compressed page exceeds its declared size")
    Output.extend(TakeSpan(Packed, Position, Count, "compressed literal run"))
    return Position + Count
