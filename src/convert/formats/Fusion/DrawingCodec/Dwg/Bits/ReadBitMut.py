from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor


def ReadBitMut(Cursor: BitCursor) -> int:
    return Cursor.TakeBits(1)
