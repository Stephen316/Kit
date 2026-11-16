from dataclasses import dataclass as MakeDataClass
from typing import Generic

from convert.Formats.Fusion.EntityCodec.Model.MemberValue import KMemberValue


# named value needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class NamedValue(Generic[KMemberValue]):
    FieldName: str
    Value: KMemberValue
