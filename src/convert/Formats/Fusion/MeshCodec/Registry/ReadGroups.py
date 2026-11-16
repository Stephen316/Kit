from convert.Formats.Fusion.MeshCodec.Model.FaceGroup import FaceGroup
from convert.Formats.Fusion.MeshCodec.Wire.ProtoBytes import ProtoBytes
from convert.Formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField
from convert.Formats.Fusion.MeshCodec.Wire.ProtoNumber import ProtoNumber
from convert.Formats.Fusion.MeshCodec.Wire.ProtoText import ProtoText
from convert.Formats.Fusion.MeshCodec.Wire.SelectFields import SelectFields


# the groups operation needs a distinct decoding boundary so vertex and index streams retain their intended connectivity
def ReadGroups(Fields: tuple[ProtoField, ...]) -> tuple[FaceGroup, ...]:
    Result: list[FaceGroup] = []
    for Field in Fields:
        if Field.Number != 6:
            raise ValueError("Unsupported Fusion mesh group declaration")
        KeyField, IdField = SelectFields(ProtoBytes(Field), (1, 2))
        Result.append(FaceGroup(ProtoNumber(KeyField), ProtoText(IdField)))
    return tuple(Result)
