from typing import Generic, TypedDict, TypeVar

# field wire must remain consistent across callers so entity identifiers retain their schema and reference meaning
KFieldWire = TypeVar("KFieldWire")


# field json needs an explicit state contract so entity identifiers retain their schema and reference meaning
class FieldJson(TypedDict, Generic[KFieldWire]):
    FieldName: str
    ValueType: KFieldWire
    IsSaved: bool
