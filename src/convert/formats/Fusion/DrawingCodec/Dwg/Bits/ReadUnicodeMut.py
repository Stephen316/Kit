from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitShortMut import (
    ReadBitShortMut,
)


def ReadUnicodeMut(Cursor: BitCursor) -> str:
    Count = ReadBitShortMut(Cursor)
    if Count * 16 > Cursor.Limit - Cursor.Position:
        raise ValueError("DWG unicode text exceeds its string stream")
    Encoded = Cursor.TakeBits(Count * 16).to_bytes(Count * 2, "big")
    try:
        return Encoded.decode("utf-16-le")
    except UnicodeDecodeError as ErrorInfo:
        raise ValueError("DWG unicode text is not valid UTF-16") from ErrorInfo
