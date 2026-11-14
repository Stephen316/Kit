from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue


def JsonObject(Value: KJsonValue, Fields: str) -> dict[str, KJsonValue]:
    if not isinstance(Value, dict) or set(Value) != set(Fields.split()):
        raise ValueError("Unsupported Fusion bundle object fields")
    return Value


def JsonArray(Value: KJsonValue) -> list[KJsonValue]:
    if not isinstance(Value, list) or len(Value) > 4094:
        raise ValueError("Invalid or oversized Fusion bundle array")
    return Value
