from convert.Formats.Fusion.MeshCodec.Wire.EmitVarint import EmitVarint
from convert.Formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField


# the proto operation needs a consistent construction rule so vertex and index streams retain their intended connectivity
def EmitProto(Fields: tuple[ProtoField, ...]) -> bytes:
    Output = bytearray()
    for Field in Fields:
        if not 0 < Field.Number < 1 << 29:
            raise ValueError("Invalid Fusion mesh protobuf field")
        if isinstance(Field.Value, bytes):
            Output.extend(EmitVarint((Field.Number << 3) | 2))
            Output.extend(EmitVarint(len(Field.Value)))
            Output.extend(Field.Value)
        else:
            Output.extend(EmitVarint(Field.Number << 3))
            Output.extend(EmitVarint(Field.Value))
    return bytes(Output)
