from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor


def ReadRawShortMut(Cursor: BitCursor) -> int:
    LowByte = Cursor.TakeBits(8)
    HighByte = Cursor.TakeBits(8)
    return LowByte | HighByte << 8
