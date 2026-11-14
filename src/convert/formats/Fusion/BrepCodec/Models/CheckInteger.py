def CheckInteger(
    Value: int, Label: str, Lower: int = -(1 << 63), Upper: int = (1 << 63) - 1
) -> None:
    if type(Value) is not int or not Lower <= Value <= Upper:
        raise ValueError(f"Fusion BRep {Label} is outside its integer domain")
