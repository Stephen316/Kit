from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawShortMut import (
    ReadRawShortMut,
)


# the raw long operation needs a distinct decoding boundary so compact fields retain unambiguous bit positions
def ReadRawLongMut(Cursor: BitCursor) -> int:
    LowShort = ReadRawShortMut(Cursor)
    HighShort = ReadRawShortMut(Cursor)
    return LowShort | HighShort << 16
