from dataclasses import dataclass as MakeDataClass
from typing import Generic, TypeVar

KFieldType = TypeVar("KFieldType")


@MakeDataClass(frozen=True, slots=True)
class FieldSpec(Generic[KFieldType]):
    FieldName: str
    ValueType: KFieldType
    IsSaved: bool = True
