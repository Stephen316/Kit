from math import isfinite


# the number operation needs a distinct decoding boundary so control cage topology retains its native connectivity
def ReadNumber(Value: str) -> float:
    if len(Value) > 64:
        raise ValueError("TSM number exceeds the lexical limit")
    Result = float(Value)
    if not isfinite(Result):
        raise ValueError("TSM number is not finite")
    return Result
