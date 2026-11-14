from dataclasses import dataclass as MakeDataClass
from typing import Generic

from convert.formats.Fusion.EntityCodec.Model.MemberValue import KMemberValue
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue


@MakeDataClass(frozen=True, slots=True)
class ValueStruct(Generic[KMemberValue]):
    Fields: tuple[NamedValue[KMemberValue], ...]
