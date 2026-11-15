from convert.formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField
from convert.formats.Fusion.MeshCodec.Wire.ReadProto import ReadProto


# select fields must resolve unambiguously so vertex and index streams retain their intended connectivity
def SelectFields(Payload: bytes, Expected: tuple[int, ...]) -> tuple[ProtoField, ...]:
    Fields = ReadProto(Payload)
    if sorted(Field.Number for Field in Fields) != sorted(Expected):
        raise ValueError("Unsupported Fusion mesh registry fields")

    # ordering by field number must stay deterministic so mesh reconstruction resolves equivalent inputs consistently
    return tuple(sorted(Fields, key=lambda Field: Field.Number))
