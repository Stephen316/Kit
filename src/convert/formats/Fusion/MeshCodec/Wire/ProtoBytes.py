from convert.formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField


def ProtoBytes(Field: ProtoField) -> bytes:
    if not isinstance(Field.Value, bytes):
        raise ValueError("Expected Fusion mesh protobuf bytes")
    return Field.Value
