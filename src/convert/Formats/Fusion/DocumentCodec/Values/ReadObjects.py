from typing import cast as CastValue


# the object operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadObject(Value: object) -> dict[str, object]:
    if not isinstance(Value, dict):
        raise ValueError("Expected named semantic fields")
    Fields = CastValue(dict[object, object], Value)
    if any(not isinstance(FieldName, str) for FieldName in Fields):
        raise ValueError("Semantic field names must be strings")
    return CastValue(dict[str, object], Value)


# the series operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadSeries(Value: object) -> list[object]:
    if not isinstance(Value, list):
        raise ValueError("Expected a semantic value sequence")
    return CastValue(list[object], Value)


# the string operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadString(Value: object) -> str:
    if not isinstance(Value, str):
        raise ValueError("Expected a semantic string")
    return Value


# the integer operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadInteger(Value: object) -> int:
    if type(Value) is not int:
        raise ValueError("Expected a semantic integer")
    return Value


# the true value decision must stay consistent so model state retains its native feature and ownership relationships
def IsTrueValue(Value: object) -> bool:
    if type(Value) is not bool:
        raise ValueError("Expected a semantic boolean")
    return Value
