from convert.Formats.Fusion.MeshCodec.Wire.EmitMapAtom import EmitMapAtom


# the map operation needs a consistent construction rule so vertex and index streams retain their intended connectivity
def EmitMap(Values: dict[str, int | bool]) -> bytes:
    if len(Values) > 15:
        raise ValueError("Unsupported Fusion mesh MessagePack map size")
    return bytes((128 + len(Values),)) + b"".join(
        EmitMapAtom(KeyName) + EmitMapAtom(Value) for KeyName, Value in Values.items()
    )
