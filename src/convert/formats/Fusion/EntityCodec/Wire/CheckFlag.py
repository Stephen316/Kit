def CheckFlag(Value: object) -> None:
    if type(Value) is not bool:
        raise ValueError("Fusion entity flag requires a boolean")
