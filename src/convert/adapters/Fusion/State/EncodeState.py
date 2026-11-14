from base64 import b64encode as EncodeBase
from collections.abc import Mapping
from dataclasses import fields as DataFields
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.Fusion.State.StateTypes import KStateTypes


def EncodeState(Value: object, Depth: int = 0) -> object:
    if Depth > 64:
        raise ValueError("Fusion semantic state exceeds nesting limit")
    if Value is None or type(Value) in (str, int, bool):
        return Value
    if type(Value) is float and IsFinite(Value):
        return Value
    if type(Value) in KStateTypes:
        ClassName = f"{type(Value).__module__}.{type(Value).__name__}"
        if isinstance(Value, EnumBase):
            return {"enum": ClassName, "value": Value.value}
        if IsDataClass(Value) and not isinstance(Value, type):
            return {
                "record": ClassName,
                "fields": {
                    Field.name: EncodeState(getattr(Value, Field.name), Depth + 1)
                    for Field in DataFields(Value)
                },
            }
    if isinstance(Value, bytes) and len(Value) <= 2000000:
        return {"bytes": EncodeBase(Value).decode("ascii")}
    if isinstance(Value, tuple):
        return {
            "tuple": [
                EncodeState(ItemValue, Depth + 1)
                for ItemValue in CastValue(tuple[object, ...], Value)
            ]
        }
    if isinstance(Value, Mapping) and all(
        isinstance(FieldKey, str)
        for FieldKey in CastValue(Mapping[object, object], Value)
    ):
        return {
            "map": {
                FieldKey: EncodeState(ItemValue, Depth + 1)
                for FieldKey, ItemValue in CastValue(
                    Mapping[str, object], Value
                ).items()
            }
        }
    raise ValueError("Unsupported Fusion semantic-state value")
