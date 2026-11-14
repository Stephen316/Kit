from struct import pack as PackValue

from convert.formats.Fusion.BrepCodec.Wire.EncodeBrepValue import EncodeBrepValue
from convert.formats.Fusion.GeometryCodec.GeometryFields import KVectorFields
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


def EncodeConeValue(Value: KGeometryValue, NameValue: str, Index: int) -> bytes:
    if isinstance(Value, tuple):
        TagValue = KVectorFields[(NameValue, Index)][0]
        return bytes((TagValue,)) + PackValue("<3d", *Value)
    if (NameValue, Index) == ("cone-surface", 11):
        if type(Value) is not float:
            raise ValueError("Frustum parameter scale must be a double")
        return b"\x06" + PackValue("<d", Value)
    return EncodeBrepValue(Value, NameValue, Index)
