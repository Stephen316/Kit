from convert.formats.Fusion.GeometryCodec.EncodeSmbValue import EncodeSmbValue
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


# the boundary representation value operation needs a consistent construction rule so topology identity survives native history reconstruction
def EncodeBrepValue(Value: KGeometryValue, NameValue: str, Index: int) -> bytes:
    if isinstance(Value, bool):
        return b"\x0a" if Value else b"\x0b"
    return EncodeSmbValue(Value, NameValue, Index)
