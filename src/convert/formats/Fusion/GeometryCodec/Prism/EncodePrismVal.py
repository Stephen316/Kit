from struct import pack as PackValue

from convert.formats.Fusion.GeometryCodec.EncodeSmbValue import EncodeSmbValue
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


def EncodePrismVal(Value: KGeometryValue, NameValue: str, Index: int) -> bytes:
    if NameValue == "straight-curve" and Index in (3, 4):
        if not isinstance(Value, tuple) or len(Value) != 3:
            raise ValueError("Prism line requires an origin and a displacement vector")
        return bytes((19 if Index == 3 else 20,)) + PackValue(
            "<3d", *(Member / 10 for Member in Value)
        )
    return EncodeSmbValue(Value, NameValue, Index)
