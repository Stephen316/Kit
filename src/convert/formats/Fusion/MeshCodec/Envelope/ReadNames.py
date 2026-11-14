from convert.formats.Fusion.MeshCodec.Wire.ReadMap import ReadMap


def ReadNames(Payload: bytes) -> tuple[str, ...]:
    Values = ReadMap(Payload)
    if len(Values) != 6 or any(type(Value) is not int for Value in Values.values()):
        raise ValueError("Unsupported Fusion mesh stream identity table")
    if sorted(Values.values()) != list(range(2, 8)):
        raise ValueError("Fusion mesh stream identities are not unique chunk ordinals")
    return tuple(sorted(Values, key=lambda KeyName: Values[KeyName]))
