def StateFlag(Value: bool) -> int:
    if type(Value) is not bool:
        raise ValueError("Fusion journal state flag requires a boolean")
    return int(Value)
