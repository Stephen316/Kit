from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter


def PutBytesMut(Writer: BitWriter, DataValue: bytes) -> None:
    if DataValue:
        Writer.PutBits(int.from_bytes(DataValue, "big"), len(DataValue) * 8)


def PutRawCharMut(Writer: BitWriter, Value: int) -> None:
    Writer.PutBits(Value, 8)


def PutRawShortMut(Writer: BitWriter, Value: int) -> None:
    PutBytesMut(Writer, PackFields("<H", Value))


def PutRawLongMut(Writer: BitWriter, Value: int) -> None:
    PutBytesMut(Writer, PackFields("<I", Value))


def PutRawDblMut(Writer: BitWriter, Value: float) -> None:
    PutBytesMut(Writer, PackFields("<d", Value))
