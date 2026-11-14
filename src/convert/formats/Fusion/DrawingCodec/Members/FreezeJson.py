from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.DrawingCodec.Members.JsonFields import (
    JsonFields,
    KFrozenJson,
)


def FreezeJson(Value: KJsonValue) -> KFrozenJson:
    if isinstance(Value, dict):
        return JsonFields(
            tuple(
                (KeyValue, FreezeJson(ItemValue))
                for KeyValue, ItemValue in Value.items()
            )
        )
    if isinstance(Value, list):
        return tuple(FreezeJson(ItemValue) for ItemValue in Value)
    return Value


def ThawJson(Value: KFrozenJson) -> KJsonValue:
    if isinstance(Value, JsonFields):
        Result: dict[str, KJsonValue] = {}
        for KeyValue, ItemValue in Value.Items:
            if type(KeyValue) is not str or KeyValue in Result:
                raise ValueError("Invalid or duplicate Fusion drawing JSON key")
            Result[KeyValue] = ThawJson(ItemValue)
        return Result
    if isinstance(Value, tuple):
        return [ThawJson(ItemValue) for ItemValue in Value]
    if Value is None or type(Value) in (bool, int, float, str):
        return Value
    raise ValueError("Unsupported Fusion drawing JSON value")
