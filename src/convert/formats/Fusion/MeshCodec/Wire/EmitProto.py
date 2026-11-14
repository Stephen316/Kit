from convert.formats.Fusion.MeshCodec.Wire.EmitVarint import EmitVarint
from convert.formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField


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
