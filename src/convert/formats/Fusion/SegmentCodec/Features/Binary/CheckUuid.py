from uuid import UUID as UuidValue


def CheckUuid(Value: str) -> None:
    if type(Value) is not str or len(Value) != 36:
        raise ValueError("Invalid Fusion feature UUID text")
    try:
        Canonical = str(UuidValue(Value))
    except ValueError as ErrorInfo:
        raise ValueError("Invalid Fusion feature UUID") from ErrorInfo
    if Value != Canonical:
        raise ValueError("Fusion feature UUID requires canonical lowercase text")
