from re import fullmatch


def ReadInteger(Value: str) -> int:
    if len(Value) > 11 or fullmatch(r"-?[0-9]+", Value) is None:
        raise ValueError("Invalid TSM integer")
    Result = int(Value)
    if not -1 <= Result <= 2147483647:
        raise ValueError("TSM integer exceeds the qualified range")
    return Result
