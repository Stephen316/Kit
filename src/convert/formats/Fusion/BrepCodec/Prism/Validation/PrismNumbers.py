from math import isfinite as IsFinite


def CheckReal(Value: float) -> None:
    if isinstance(Value, bool) or not IsFinite(Value):
        raise ValueError("Prism history requires finite real geometry")


def CheckVector(Value: tuple[float, float, float]) -> None:
    if type(Value) is not tuple or len(Value) != 3:
        raise ValueError("Prism history requires three-component vectors")
    for Member in Value:
        CheckReal(Member)


def DotPrism(
    First: tuple[float, float, float], Second: tuple[float, float, float]
) -> float:
    return sum(
        FirstValue * SecondValue
        for FirstValue, SecondValue in zip(First, Second, strict=True)
    )
