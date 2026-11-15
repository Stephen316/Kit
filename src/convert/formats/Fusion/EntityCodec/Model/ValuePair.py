from dataclasses import dataclass as MakeDataClass
from typing import Generic

from convert.formats.Fusion.EntityCodec.Model.MemberValue import KMemberValue


# value pair needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class ValuePair(Generic[KMemberValue]):
    First: KMemberValue
    Second: KMemberValue
