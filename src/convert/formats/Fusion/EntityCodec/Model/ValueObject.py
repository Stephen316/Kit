from dataclasses import dataclass as MakeDataClass
from typing import Generic

from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.MemberValue import KMemberValue


@MakeDataClass(frozen=True, slots=True)
class ValueObject(Generic[KMemberValue]):
    Groups: tuple[EntityGroup[KMemberValue], ...]
