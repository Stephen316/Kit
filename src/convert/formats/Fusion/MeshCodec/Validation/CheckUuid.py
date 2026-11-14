from uuid import UUID as UuidValue


def CheckUuid(Value: str) -> None:
    if str(UuidValue(Value)).lower() != Value.lower():
        raise ValueError("Invalid Fusion mesh UUID")
