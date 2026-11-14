from collections.abc import Mapping
from json import dumps as JsonDumps
from typing import cast as CastValue

from convert.adapters.Fusion.State.DecodeState import DecodeState


def CheckContract(Value: object, FieldName: str, Version: int = 1) -> object:
    if not isinstance(Value, Mapping):
        raise ValueError("Fusion conversion requires a versioned semantic contract")
    Fields = CastValue(Mapping[str, object], Value)
    if (
        set(Fields) != {"version", FieldName}
        or type(Fields["version"]) is not int
        or Fields["version"] != Version
    ):
        raise ValueError("Unsupported Fusion semantic contract version or fields")
    if len(JsonDumps(Fields[FieldName], allow_nan=False)) > 64000000:
        raise ValueError("Fusion semantic contract exceeds size limit")
    return DecodeState(Fields[FieldName])
