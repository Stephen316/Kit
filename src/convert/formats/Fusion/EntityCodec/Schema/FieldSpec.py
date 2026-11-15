from dataclasses import dataclass as MakeDataClass
from typing import Generic, TypeVar

# field type must remain consistent across callers so entity identifiers retain their schema and reference meaning
KFieldType = TypeVar("KFieldType")


# field specification needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class FieldSpec(Generic[KFieldType]):
    FieldName: str
    ValueType: KFieldType
    IsSaved: bool = True
