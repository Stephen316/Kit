from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue


def JsonString(Value: KJsonValue) -> str:
    if not isinstance(Value, str) or len(Value.encode("utf-8")) > 1024 * 1024:
        raise ValueError("Invalid or oversized Fusion bundle string")
    return Value


def JsonInteger(Value: KJsonValue) -> int:
    if type(Value) is not int or not 0 <= Value <= (1 << 53) - 1:
        raise ValueError("Invalid Fusion bundle integer")
    return Value
