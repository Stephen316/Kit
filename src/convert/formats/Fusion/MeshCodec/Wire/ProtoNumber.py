from convert.formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField


# proto number needs an explicit validity boundary so vertex and index streams retain their intended connectivity
def ProtoNumber(Field: ProtoField) -> int:
    if type(Field.Value) is not int or not 0 <= Field.Value < 1 << 32:
        raise ValueError("Expected Fusion mesh uint32")
    return Field.Value
