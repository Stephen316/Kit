from struct import pack as PackValue

from convert.formats.Fusion.GeometryCodec.EncodeSmbString import EncodeSmbString
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


def EmitSmbHeader(Stamp: GeometryStamp) -> bytes:
    Header = b"ASM BinaryFile8" + PackValue("<4q", 23200, 0, 2, 2)
    Strings = b"".join(
        EncodeSmbString(7, Value)
        for Value in (Stamp.Product, Stamp.Version, Stamp.SavedAt)
    )
    Doubles = b"".join(
        b"\x06" + PackValue("<d", Value) for Value in (10.0, 1e-6, 1e-10)
    )
    return Header + Strings + Doubles
