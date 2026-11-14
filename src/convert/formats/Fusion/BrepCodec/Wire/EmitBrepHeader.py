from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KIntCodes
from struct import pack as PackValue

from convert.formats.Fusion.GeometryCodec.EncodeSmbString import EncodeSmbString
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


def EmitBrepHeader(
    Stamp: GeometryStamp,
    RootCount: int,
    HasHistory: bool,
    ScaleValue: float,
    Width: int = 8,
) -> bytes:
    Prefix = b"ASM BinaryFile" + str(Width).encode("ascii")
    Prefix += PackValue(
        "<4" + KIntCodes[Width][1], 23200, 0, RootCount, 3 if HasHistory else 2
    )
    Strings = b"".join(EncodeSmbString(7, Value) for Value in (Stamp.Product, Stamp.Version, Stamp.SavedAt))
    Doubles = b"".join(b"\x06" + PackValue("<d", Value) for Value in (ScaleValue, 1e-6, 1e-10))
    return Prefix + Strings + Doubles
