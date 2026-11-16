from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor


# the raw char operation needs a distinct decoding boundary so compact fields retain unambiguous bit positions
def ReadRawCharMut(Cursor: BitCursor) -> int:
    return Cursor.TakeBits(8)
