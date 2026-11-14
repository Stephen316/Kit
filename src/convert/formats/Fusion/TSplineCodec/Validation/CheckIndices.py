def CheckIndices(
    Values: tuple[int, ...], Limit: int, KindValue: str, IsUnique: bool = True
) -> None:
    if any(type(Value) is not int or not 0 <= Value < Limit for Value in Values):
        raise ValueError("Invalid TSM " + KindValue + " reference")
    if IsUnique and len(set(Values)) != len(Values):
        raise ValueError("Repeated TSM " + KindValue + " reference")
