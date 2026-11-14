from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutRawMut import (
    PutBytesMut,
    PutRawCharMut,
    PutRawDblMut,
    PutRawLongMut,
    PutRawShortMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef

KOneBits = PackFields("<d", 1.0)
KZeroBits = PackFields("<d", 0.0)


def PutBitShortMut(Writer: BitWriter, Value: int) -> None:
    if Value == 0:
        Writer.PutBits(2, 2)
    elif Value == 256:
        Writer.PutBits(3, 2)
    elif Value < 256:
        Writer.PutBits(1, 2)
        PutRawCharMut(Writer, Value)
    else:
        Writer.PutBits(0, 2)
        PutRawShortMut(Writer, Value)


def PutBitLongMut(Writer: BitWriter, Value: int) -> None:
    if Value == 0:
        Writer.PutBits(2, 2)
    elif Value < 256:
        Writer.PutBits(1, 2)
        PutRawCharMut(Writer, Value)
    else:
        Writer.PutBits(0, 2)
        PutRawLongMut(Writer, Value)


def PutBitLLMut(Writer: BitWriter, Value: int) -> None:
    ByteCount = (Value.bit_length() + 7) // 8
    Writer.PutBits(ByteCount, 3)
    PutBytesMut(Writer, Value.to_bytes(ByteCount, "little"))


def PutBitDblMut(Writer: BitWriter, Value: float) -> None:
    Packed = PackFields("<d", Value)
    if Packed == KOneBits:
        Writer.PutBits(1, 2)
    elif Packed == KZeroBits:
        Writer.PutBits(2, 2)
    else:
        Writer.PutBits(0, 2)
        PutRawDblMut(Writer, Value)


def PutDefDblMut(Writer: BitWriter, Value: float, Default: float) -> None:
    Packed = PackFields("<d", Value)
    BaseBits = PackFields("<d", Default)
    if Packed == BaseBits:
        Writer.PutBits(0, 2)
    elif Packed[4:] == BaseBits[4:]:
        Writer.PutBits(1, 2)
        PutBytesMut(Writer, Packed[0:4])
    elif Packed[6:] == BaseBits[6:]:
        Writer.PutBits(2, 2)
        PutBytesMut(Writer, Packed[4:6] + Packed[0:4])
    else:
        Writer.PutBits(3, 2)
        PutBytesMut(Writer, Packed)


def PutHandleMut(Writer: BitWriter, Reference: DwgHandleRef) -> None:
    ByteCount = (Reference.RefValue.bit_length() + 7) // 8
    Writer.PutBits(Reference.RefCode, 4)
    Writer.PutBits(ByteCount, 4)
    Writer.PutBits(Reference.RefValue, 8 * ByteCount)


def PutUnicodeMut(Writer: BitWriter, TextValue: str) -> None:
    Encoded = TextValue.encode("utf-16-le")
    PutBitShortMut(Writer, len(Encoded) // 2)
    PutBytesMut(Writer, Encoded)


def PutObjTypeMut(Writer: BitWriter, Value: int) -> None:
    if Value < 0x100:
        Writer.PutBits(0, 2)
        PutRawCharMut(Writer, Value)
    elif 0x1F0 <= Value < 0x2F0:
        Writer.PutBits(1, 2)
        PutRawCharMut(Writer, Value - 0x1F0)
    else:
        Writer.PutBits(2, 2)
        PutRawShortMut(Writer, Value)
