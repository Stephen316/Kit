from struct import pack as PackValue

from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.EncodeSmbString import EncodeSmbString
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryFields import KLengthScalars
from convert.formats.Fusion.GeometryCodec.GeometryFields import KVectorFields
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken


def EncodeSmbValue(Value: KGeometryValue, NameValue: str, Index: int) -> bytes:
    if isinstance(Value, EntityRef):
        return b"\x0c" + PackValue("<q", Value.Index)
    if isinstance(Value, CountedText):
        return EncodeSmbString(7, Value.Value)
    if isinstance(Value, KeywordToken):
        return b"\x0a" if Value.Value == "reversed" else b"\x0b"
    if isinstance(Value, int) and (NameValue, Index) not in KLengthScalars:
        return b"\x04" + PackValue("<q", Value)
    if isinstance(Value, tuple):
        TagValue, Divisor = KVectorFields[(NameValue, Index)]
        Values = tuple(Member / Divisor for Member in Value)
        return bytes((TagValue,)) + PackValue("<3d", *Values)
    Divisor = 10 if (NameValue, Index) in KLengthScalars else 1
    return b"\x06" + PackValue("<d", Value / Divisor)
