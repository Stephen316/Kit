from dataclasses import dataclass as MakeDataClass
from typing import Generic

from convert.Formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.Formats.Fusion.EntityCodec.Model.MemberValue import KMemberValue


# value object needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class ValueObject(Generic[KMemberValue]):
    Groups: tuple[EntityGroup[KMemberValue], ...]
