from collections.abc import Iterable
from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from typing import TypeVar, cast as CastValue

KFoundValue = TypeVar("KFoundValue")


def FindValues(Value: object, KindValue: type[KFoundValue]) -> list[KFoundValue]:
    Found: list[KFoundValue] = [Value] if isinstance(Value, KindValue) else []
    Children: Iterable[object] = ()
    if IsDataClass(Value) and not isinstance(Value, type):
        Children = [getattr(Value, FieldValue.name) for FieldValue in DataFields(Value)]
    elif isinstance(Value, (tuple, list)):
        Children = CastValue(Iterable[object], Value)
    elif isinstance(Value, dict):
        Children = CastValue(dict[object, object], Value).values()
    for ItemValue in Children:
        Found.extend(FindValues(ItemValue, KindValue))
    return Found
