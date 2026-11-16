from struct import pack as PackFields

from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter


# the bytes operation needs a consistent construction rule so compact fields retain unambiguous bit positions
def PutBytesMut(Writer: BitWriter, DataValue: bytes) -> None:
    if DataValue:
        Writer.PutBits(int.from_bytes(DataValue, "big"), len(DataValue) * 8)


# the raw char operation needs a consistent construction rule so compact fields retain unambiguous bit positions
def PutRawCharMut(Writer: BitWriter, Value: int) -> None:
    Writer.PutBits(Value, 8)


# the raw short operation needs a consistent construction rule so compact fields retain unambiguous bit positions
def PutRawShortMut(Writer: BitWriter, Value: int) -> None:
    PutBytesMut(Writer, PackFields("<H", Value))


# the raw long operation needs a consistent construction rule so compact fields retain unambiguous bit positions
def PutRawLongMut(Writer: BitWriter, Value: int) -> None:
    PutBytesMut(Writer, PackFields("<I", Value))


# the raw dbl operation needs a consistent construction rule so compact fields retain unambiguous bit positions
def PutRawDblMut(Writer: BitWriter, Value: float) -> None:
    PutBytesMut(Writer, PackFields("<d", Value))
