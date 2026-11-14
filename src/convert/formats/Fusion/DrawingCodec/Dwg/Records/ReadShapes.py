from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadCodeMut import (
    ReadBitDblMut,
    ReadRawDblMut,
)


def ReadOneBitMut(Cursor: BitCursor) -> int:
    return Cursor.TakeBits(1)


def ReadTwoBitsMut(Cursor: BitCursor) -> int:
    return Cursor.TakeBits(2)


def ReadRawXyMut(Cursor: BitCursor) -> tuple[float, ...]:
    return tuple(ReadRawDblMut(Cursor) for _ in range(2))


def ReadRawXyzMut(Cursor: BitCursor) -> tuple[float, ...]:
    return tuple(ReadRawDblMut(Cursor) for _ in range(3))


def ReadBitXyMut(Cursor: BitCursor) -> tuple[float, ...]:
    return tuple(ReadBitDblMut(Cursor) for _ in range(2))


def ReadBitXyzMut(Cursor: BitCursor) -> tuple[float, ...]:
    return tuple(ReadBitDblMut(Cursor) for _ in range(3))


def ReadExtrudeMut(Cursor: BitCursor) -> tuple[float, ...]:
    if Cursor.TakeBits(1):
        return (0.0, 0.0, 1.0)
    return ReadBitXyzMut(Cursor)


def ReadThickMut(Cursor: BitCursor) -> float:
    if Cursor.TakeBits(1):
        return 0.0
    return ReadBitDblMut(Cursor)
