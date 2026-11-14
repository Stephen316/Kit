from json import JSONDecodeError, loads as LoadJson
from typing import cast as CastValue

from convert.formats.Fusion.BundleCodec.Json.JsonLimits import CheckJsonTree
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue


def UniqueObject(Pairs: list[tuple[str, KJsonValue]]) -> dict[str, KJsonValue]:
    Result: dict[str, KJsonValue] = {}
    for FieldName, Value in Pairs:
        if FieldName in Result:
            raise ValueError("Duplicate Fusion bundle JSON key")
        Result[FieldName] = Value
    return Result


def RejectNumber(Value: str) -> None:
    raise ValueError(f"Invalid Fusion bundle JSON number: {Value}")


def ReadJson(DataValue: bytes) -> KJsonValue:
    if len(DataValue) > 4 * 1024 * 1024:
        raise ValueError("Fusion bundle JSON exceeds byte limit")
    try:
        Result = CastValue(
            KJsonValue,
            LoadJson(
                DataValue.decode("utf-8"),
                object_pairs_hook=UniqueObject,
                parse_constant=RejectNumber,
            ),
        )
        CheckJsonTree(Result)
        return Result
    except (UnicodeError, JSONDecodeError, RecursionError) as ErrorInfo:
        raise ValueError("Malformed Fusion bundle JSON") from ErrorInfo
