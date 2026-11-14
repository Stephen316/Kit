from math import isfinite


def ReadNumber(Value: str) -> float:
    if len(Value) > 64:
        raise ValueError("TSM number exceeds the lexical limit")
    Result = float(Value)
    if not isfinite(Result):
        raise ValueError("TSM number is not finite")
    return Result
