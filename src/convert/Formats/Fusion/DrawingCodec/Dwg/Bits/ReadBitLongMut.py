from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawCharMut import ReadRawCharMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawLongMut import ReadRawLongMut


# the bit long operation needs a distinct decoding boundary so compact fields retain unambiguous bit positions
def ReadBitLongMut(Cursor: BitCursor) -> int:
    CodeBits = Cursor.TakeBits(2)
    if CodeBits == 0:
        return ReadRawLongMut(Cursor)
    if CodeBits == 1:
        return ReadRawCharMut(Cursor)
    if CodeBits == 2:
        return 0
    raise ValueError("DWG bit long uses the reserved size code")
