from convert.formats.Fusion.GeometryCodec.EncodeSmbValue import EncodeSmbValue
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


def EncodeBrepValue(Value: KGeometryValue, NameValue: str, Index: int) -> bytes:
    if isinstance(Value, bool):
        return b"\x0a" if Value else b"\x0b"
    return EncodeSmbValue(Value, NameValue, Index)
