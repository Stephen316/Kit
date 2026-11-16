# state flag needs an explicit validity boundary so revision ownership survives native history reconstruction
def StateFlag(Value: bool) -> int:
    if type(Value) is not bool:
        raise ValueError("Fusion journal state flag requires a boolean")
    return int(Value)
