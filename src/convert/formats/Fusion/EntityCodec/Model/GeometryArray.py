from dataclasses import dataclass as MakeDataClass
from typing import Generic

from convert.formats.Fusion.EntityCodec.Model.MemberValue import KMemberValue


@MakeDataClass(frozen=True, slots=True)
class GeometryArray(Generic[KMemberValue]):
    PhysicalLength: int
    GrowLength: int
    Values: tuple[KMemberValue, ...]
