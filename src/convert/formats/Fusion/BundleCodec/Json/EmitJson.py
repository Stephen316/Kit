from json import dumps as DumpJson

from convert.formats.Fusion.BundleCodec.Json.JsonLimits import CheckJsonTree
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue


def EmitJson(Value: KJsonValue) -> bytes:
    CheckJsonTree(Value)
    Result = DumpJson(
        Value, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(Result) > 4 * 1024 * 1024:
        raise ValueError("Fusion bundle JSON exceeds byte limit")
    return Result
