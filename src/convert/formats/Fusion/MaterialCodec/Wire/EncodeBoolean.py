def EncodeBoolean(Value: bool) -> bytes:
    if type(Value) is not bool:
        raise ValueError("Fusion material flag must be a boolean")
    return bytes((Value,))
