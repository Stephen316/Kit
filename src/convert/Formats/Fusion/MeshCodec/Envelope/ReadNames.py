from convert.Formats.Fusion.MeshCodec.Wire.ReadMap import ReadMap


# the names operation needs a distinct decoding boundary so vertex and index streams retain their intended connectivity
def ReadNames(Payload: bytes) -> tuple[str, ...]:
    Values = ReadMap(Payload)
    if len(Values) != 6 or any(type(Value) is not int for Value in Values.values()):
        raise ValueError("Unsupported Fusion mesh stream identity table")
    if sorted(Values.values()) != list(range(2, 8)):
        raise ValueError("Fusion mesh stream identities are not unique chunk ordinals")

    # ordering by values key name must stay deterministic so mesh reconstruction resolves equivalent inputs consistently
    return tuple(sorted(Values, key=lambda KeyName: Values[KeyName]))
