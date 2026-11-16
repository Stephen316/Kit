from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor


# the raw short operation needs a distinct decoding boundary so compact fields retain unambiguous bit positions
def ReadRawShortMut(Cursor: BitCursor) -> int:
    LowByte = Cursor.TakeBits(8)
    HighByte = Cursor.TakeBits(8)
    return LowByte | HighByte << 8
