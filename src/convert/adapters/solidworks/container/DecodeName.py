from convert.adapters.solidworks.container.RotateBytes import RotateBytes


# the name operation needs a distinct decoding boundary so stream contents retain their geometry and feature relationships
def DecodeName(Payload: bytes, Version: int) -> str | None:
    try:
        NameValue = RotateBytes(Payload, Version).decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not NameValue or any(ord(Character) < 32 for Character in NameValue):
        return None
    return NameValue
