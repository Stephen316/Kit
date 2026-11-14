from struct import pack as PackFields
from struct import unpack as UnpackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawShortMut import (
    ReadRawShortMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef


def ReadRawDblMut(Cursor: BitCursor) -> float:
    Packed = Cursor.TakeBits(64).to_bytes(8, "big")
    return float(UnpackFields("<d", Packed)[0])


def ReadBitDblMut(Cursor: BitCursor) -> float:
    CodeBits = Cursor.TakeBits(2)
    if CodeBits == 0:
        return ReadRawDblMut(Cursor)
    if CodeBits == 3:
        raise ValueError("DWG bit double uses the reserved size code")
    return 1.0 if CodeBits == 1 else 0.0


def ReadDefDblMut(Cursor: BitCursor, Default: float) -> float:
    CodeBits = Cursor.TakeBits(2)
    if CodeBits == 0:
        return Default
    if CodeBits == 3:
        return ReadRawDblMut(Cursor)
    Packed = bytearray(PackFields("<d", Default))
    if CodeBits == 1:
        Packed[0:4] = Cursor.TakeBits(32).to_bytes(4, "big")
    else:
        PatchBytes = Cursor.TakeBits(48).to_bytes(6, "big")
        Packed[4:6] = PatchBytes[0:2]
        Packed[0:4] = PatchBytes[2:6]
    return float(UnpackFields("<d", bytes(Packed))[0])


def ReadBitLLMut(Cursor: BitCursor) -> int:
    ByteCount = Cursor.TakeBits(3)
    Value = 0
    for Index in range(ByteCount):
        Value |= Cursor.TakeBits(8) << 8 * Index
    return Value


def ReadHandleMut(Cursor: BitCursor) -> DwgHandleRef:
    RefCode = Cursor.TakeBits(4)
    ByteCount = Cursor.TakeBits(4)
    return DwgHandleRef(RefCode, Cursor.TakeBits(8 * ByteCount))


def ReadObjTypeMut(Cursor: BitCursor) -> int:
    CodeBits = Cursor.TakeBits(2)
    if CodeBits == 0:
        return Cursor.TakeBits(8)
    if CodeBits == 1:
        return Cursor.TakeBits(8) + 0x1F0
    return ReadRawShortMut(Cursor)
