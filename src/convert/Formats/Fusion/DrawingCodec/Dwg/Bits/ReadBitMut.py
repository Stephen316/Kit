from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor


# the bit operation needs a distinct decoding boundary so compact fields retain unambiguous bit positions
def ReadBitMut(Cursor: BitCursor) -> int:
    return Cursor.TakeBits(1)
