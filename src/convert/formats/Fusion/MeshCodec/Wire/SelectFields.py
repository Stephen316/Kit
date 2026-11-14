from convert.formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField
from convert.formats.Fusion.MeshCodec.Wire.ReadProto import ReadProto


def SelectFields(Payload: bytes, Expected: tuple[int, ...]) -> tuple[ProtoField, ...]:
    Fields = ReadProto(Payload)
    if sorted(Field.Number for Field in Fields) != sorted(Expected):
        raise ValueError("Unsupported Fusion mesh registry fields")
    return tuple(sorted(Fields, key=lambda Field: Field.Number))
