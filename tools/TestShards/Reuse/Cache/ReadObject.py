from __future__ import annotations

from typing import cast as CastValue


def ReadObject(Value: object, Label: str) -> dict[str, object]:
    if not isinstance(Value, dict):
        raise ValueError(f"{Label} is not an object")
    Fields = CastValue(dict[object, object], Value)
    if not all(isinstance(FieldKey, str) for FieldKey in Fields):
        raise ValueError(f"{Label} has a key that is not text")
    return CastValue(dict[str, object], Fields)
