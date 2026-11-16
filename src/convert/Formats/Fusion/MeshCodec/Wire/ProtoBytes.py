from convert.Formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField


# proto bytes needs an explicit validity boundary so vertex and index streams retain their intended connectivity
def ProtoBytes(Field: ProtoField) -> bytes:
    if not isinstance(Field.Value, bytes):
        raise ValueError("Expected Fusion mesh protobuf bytes")
    return Field.Value
