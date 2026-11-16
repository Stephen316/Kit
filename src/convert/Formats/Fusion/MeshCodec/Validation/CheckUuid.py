from uuid import UUID as UuidValue


# invalid uuid input must fail here so vertex and index streams retain their intended connectivity
def CheckUuid(Value: str) -> None:
    if str(UuidValue(Value)).lower() != Value.lower():
        raise ValueError("Invalid Fusion mesh UUID")
