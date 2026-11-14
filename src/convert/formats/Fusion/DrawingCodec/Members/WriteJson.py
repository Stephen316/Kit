from json import dumps as DumpJson

from convert.formats.Fusion.BundleCodec.Json.JsonLimits import CheckJsonTree
from convert.formats.Fusion.DrawingCodec.Members.FreezeJson import ThawJson
from convert.formats.Fusion.DrawingCodec.Members.JsonFields import (
    JsonFields,
    KFrozenJson,
)
from convert.formats.Fusion.DrawingCodec.Members.JsonStyle import JsonStyle


def WriteJson(Value: KFrozenJson, Style: JsonStyle) -> bytes:
    Plain = ThawJson(Value)
    CheckJsonTree(Plain)
    if Style is JsonStyle.KCompact:
        TextValue = DumpJson(
            Plain, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        )
    elif Style is JsonStyle.KSpaced:
        TextValue = SpacedText(Value)
    else:
        raise ValueError("Unsupported Fusion drawing JSON style")
    return TextValue.encode("utf-8")


def SpacedText(Value: KFrozenJson) -> str:
    if isinstance(Value, JsonFields):
        Fields = (
            DumpJson(KeyValue, ensure_ascii=False) + " : " + SpacedText(ItemValue)
            for KeyValue, ItemValue in Value.Items
        )
        return "{" + ",".join(Fields) + "}"
    if isinstance(Value, tuple):
        return "[" + ",".join(SpacedText(ItemValue) for ItemValue in Value) + "]"
    return DumpJson(Value, ensure_ascii=False, allow_nan=False)
