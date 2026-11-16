from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadCodeMut import (
    ReadBitDblMut,
    ReadRawDblMut,
)


# the one bit operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadOneBitMut(Cursor: BitCursor) -> int:
    return Cursor.TakeBits(1)


# the two bits operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadTwoBitsMut(Cursor: BitCursor) -> int:
    return Cursor.TakeBits(2)


# the raw xy operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadRawXyMut(Cursor: BitCursor) -> tuple[float, ...]:
    return tuple(ReadRawDblMut(Cursor) for _ in range(2))


# the raw xyz operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadRawXyzMut(Cursor: BitCursor) -> tuple[float, ...]:
    return tuple(ReadRawDblMut(Cursor) for _ in range(3))


# the bit xy operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadBitXyMut(Cursor: BitCursor) -> tuple[float, ...]:
    return tuple(ReadBitDblMut(Cursor) for _ in range(2))


# the bit xyz operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadBitXyzMut(Cursor: BitCursor) -> tuple[float, ...]:
    return tuple(ReadBitDblMut(Cursor) for _ in range(3))


# the extrude operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadExtrudeMut(Cursor: BitCursor) -> tuple[float, ...]:
    if Cursor.TakeBits(1):
        return (0.0, 0.0, 1.0)
    return ReadBitXyzMut(Cursor)


# the thick operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadThickMut(Cursor: BitCursor) -> float:
    if Cursor.TakeBits(1):
        return 0.0
    return ReadBitDblMut(Cursor)
