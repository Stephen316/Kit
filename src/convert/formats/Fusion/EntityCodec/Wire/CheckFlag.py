# invalid flag input must fail here so entity identifiers retain their schema and reference meaning
def CheckFlag(Value: object) -> None:
    if type(Value) is not bool:
        raise ValueError("Fusion entity flag requires a boolean")
