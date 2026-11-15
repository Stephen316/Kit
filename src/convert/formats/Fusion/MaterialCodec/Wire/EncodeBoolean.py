# the boolean operation needs a consistent construction rule so typed appearance properties retain their native identifiers
def EncodeBoolean(Value: bool) -> bytes:
    if type(Value) is not bool:
        raise ValueError("Fusion material flag must be a boolean")
    return bytes((Value,))
