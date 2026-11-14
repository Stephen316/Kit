from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawCharMut import ReadRawCharMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawShortMut import (
    ReadRawShortMut,
)


def ReadBitShortMut(Cursor: BitCursor) -> int:
    CodeBits = Cursor.TakeBits(2)
    if CodeBits == 0:
        return ReadRawShortMut(Cursor)
    if CodeBits == 1:
        return ReadRawCharMut(Cursor)
    return 0 if CodeBits == 2 else 256
