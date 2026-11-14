from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor


def ReadRawCharMut(Cursor: BitCursor) -> int:
    return Cursor.TakeBits(8)
