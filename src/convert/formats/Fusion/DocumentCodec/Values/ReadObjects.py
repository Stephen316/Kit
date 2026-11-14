from typing import cast as CastValue


def ReadObject(Value: object) -> dict[str, object]:
    if not isinstance(Value, dict):
        raise ValueError("Expected named semantic fields")
    Fields = CastValue(dict[object, object], Value)
    if any(not isinstance(FieldName, str) for FieldName in Fields):
        raise ValueError("Semantic field names must be strings")
    return CastValue(dict[str, object], Value)


def ReadSeries(Value: object) -> list[object]:
    if not isinstance(Value, list):
        raise ValueError("Expected a semantic value sequence")
    return CastValue(list[object], Value)


def ReadString(Value: object) -> str:
    if not isinstance(Value, str):
        raise ValueError("Expected a semantic string")
    return Value


def ReadInteger(Value: object) -> int:
    if type(Value) is not int:
        raise ValueError("Expected a semantic integer")
    return Value


def IsTrueValue(Value: object) -> bool:
    if type(Value) is not bool:
        raise ValueError("Expected a semantic boolean")
    return Value
