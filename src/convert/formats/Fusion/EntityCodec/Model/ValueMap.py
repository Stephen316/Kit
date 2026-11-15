from dataclasses import dataclass as MakeDataClass
from typing import Generic

from convert.formats.Fusion.EntityCodec.Model.MemberValue import KMemberValue
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


# value map needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class ValueMap(Generic[KMemberValue]):
    Entries: tuple[ValuePair[KMemberValue], ...]
