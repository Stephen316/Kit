from math import isfinite as IsFinite

from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken


def EncodeSmtValue(Value: KGeometryValue) -> str:
    if isinstance(Value, EntityRef):
        return f"${Value.Index}"
    if isinstance(Value, CountedText):
        return f"@{len(Value.Value.encode('utf-8'))} {Value.Value}"
    if isinstance(Value, KeywordToken):
        return Value.Value
    if isinstance(Value, tuple):
        return " ".join(EncodeSmtValue(Member) for Member in Value)
    if isinstance(Value, int):
        return str(Value)
    if not IsFinite(Value):
        raise ValueError("Nonfinite SMT geometry value")
    return format(Value, ".17g")
