from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawShortMut import (
    ReadRawShortMut,
)


def ReadRawLongMut(Cursor: BitCursor) -> int:
    LowShort = ReadRawShortMut(Cursor)
    HighShort = ReadRawShortMut(Cursor)
    return LowShort | HighShort << 16
