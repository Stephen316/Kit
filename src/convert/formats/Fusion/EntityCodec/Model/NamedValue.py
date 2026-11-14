from dataclasses import dataclass as MakeDataClass
from typing import Generic

from convert.formats.Fusion.EntityCodec.Model.MemberValue import KMemberValue


@MakeDataClass(frozen=True, slots=True)
class NamedValue(Generic[KMemberValue]):
    FieldName: str
    Value: KMemberValue
