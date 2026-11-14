from dataclasses import dataclass as MakeDataClass
from typing import Generic

from convert.formats.Fusion.EntityCodec.Model.MemberValue import KMemberValue
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


@MakeDataClass(frozen=True, slots=True)
class ValueMap(Generic[KMemberValue]):
    Entries: tuple[ValuePair[KMemberValue], ...]
