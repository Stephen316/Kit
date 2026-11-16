from struct import pack as PackValue

from convert.Formats.Fusion.BrepCodec.Wire.EncodeBrepValue import EncodeBrepValue
from convert.Formats.Fusion.GeometryCodec.GeometryFields import KVectorFields
from convert.Formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


# the cone value operation needs a consistent construction rule so circular boundaries retain consistent cone and rim geometry
def EncodeConeValue(Value: KGeometryValue, NameValue: str, Index: int) -> bytes:
    if isinstance(Value, tuple):
        TagValue = KVectorFields[(NameValue, Index)][0]
        return bytes((TagValue,)) + PackValue("<3d", *Value)
    if (NameValue, Index) == ("cone-surface", 11):
        if type(Value) is not float:
            raise ValueError("Frustum parameter scale must be a double")
        return b"\x06" + PackValue("<d", Value)
    return EncodeBrepValue(Value, NameValue, Index)
