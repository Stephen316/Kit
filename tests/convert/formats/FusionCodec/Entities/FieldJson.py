from typing import Generic, TypedDict, TypeVar

# the field wire cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KFieldWire = TypeVar("KFieldWire")


# the field json boundary needs grouped coverage so repository automation cannot silently change its observable contract
class FieldJson(TypedDict, Generic[KFieldWire]):
    FieldName: str
    ValueType: KFieldWire
    IsSaved: bool
