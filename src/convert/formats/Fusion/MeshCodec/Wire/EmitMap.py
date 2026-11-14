from convert.formats.Fusion.MeshCodec.Wire.EmitMapAtom import EmitMapAtom


def EmitMap(Values: dict[str, int | bool]) -> bytes:
    if len(Values) > 15:
        raise ValueError("Unsupported Fusion mesh MessagePack map size")
    return bytes((128 + len(Values),)) + b"".join(
        EmitMapAtom(KeyName) + EmitMapAtom(Value) for KeyName, Value in Values.items()
    )
