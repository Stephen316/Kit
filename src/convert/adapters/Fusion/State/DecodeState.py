from base64 import b64decode as DecodeBase
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.Fusion.State.DecodeRecord import DecodeEnum, DecodeRecord


def DecodeState(Value: object, Depth: int = 0) -> object:
    if Depth > 64:
        raise ValueError("Fusion semantic state exceeds nesting limit")
    if Value is None or type(Value) in (str, int, bool):
        return Value
    if type(Value) is float and IsFinite(Value):
        return Value
    if not isinstance(Value, dict):
        raise ValueError("Malformed Fusion semantic state")
    Values = CastValue(dict[str, object], Value)
    if set(Values) == {"enum", "value"}:
        return DecodeEnum(Values["enum"], Values["value"])
    if set(Values) == {"record", "fields"}:
        return DecodeRecord(Values["record"], DecodeFields(Values["fields"], Depth))
    if set(Values) == {"map"}:
        return DecodeFields(Values["map"], Depth)
    if set(Values) == {"tuple"} and isinstance(Values["tuple"], list):
        return tuple(
            DecodeState(ItemValue, Depth + 1)
            for ItemValue in CastValue(list[object], Values["tuple"])
        )
    if (
        set(Values) == {"bytes"}
        and isinstance(Values["bytes"], str)
        and len(Values["bytes"]) <= 2666668
    ):
        return DecodeBase(Values["bytes"], validate=True)
    raise ValueError("Unknown Fusion semantic-state encoding")


def DecodeFields(Value: object, Depth: int) -> dict[str, object]:
    if not isinstance(Value, dict) or not all(
        isinstance(FieldKey, str) for FieldKey in CastValue(dict[object, object], Value)
    ):
        raise ValueError("Fusion semantic fields require text keys")
    return {
        FieldKey: DecodeState(ItemValue, Depth + 1)
        for FieldKey, ItemValue in CastValue(dict[str, object], Value).items()
    }
