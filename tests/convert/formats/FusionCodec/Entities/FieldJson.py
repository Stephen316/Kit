from typing import Generic, TypedDict, TypeVar

KFieldWire = TypeVar("KFieldWire")


class FieldJson(TypedDict, Generic[KFieldWire]):
    FieldName: str
    ValueType: KFieldWire
    IsSaved: bool
