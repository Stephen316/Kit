from convert.formats.Fusion.MeshCodec.Model.FaceGroup import FaceGroup
from convert.formats.Fusion.MeshCodec.Wire.ProtoBytes import ProtoBytes
from convert.formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField
from convert.formats.Fusion.MeshCodec.Wire.ProtoNumber import ProtoNumber
from convert.formats.Fusion.MeshCodec.Wire.ProtoText import ProtoText
from convert.formats.Fusion.MeshCodec.Wire.SelectFields import SelectFields


def ReadGroups(Fields: tuple[ProtoField, ...]) -> tuple[FaceGroup, ...]:
    Result: list[FaceGroup] = []
    for Field in Fields:
        if Field.Number != 6:
            raise ValueError("Unsupported Fusion mesh group declaration")
        KeyField, IdField = SelectFields(ProtoBytes(Field), (1, 2))
        Result.append(FaceGroup(ProtoNumber(KeyField), ProtoText(IdField)))
    return tuple(Result)
