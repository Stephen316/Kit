from math import isfinite as IsFinite

from convert.Formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken


# the smt value operation needs a consistent construction rule so geometric values retain their native record boundaries
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
