from convert.Formats.Fusion.MeshCodec.Model.FaceGroup import FaceGroup
from convert.Formats.Fusion.MeshCodec.Registry.ReadGroups import ReadGroups
from convert.Formats.Fusion.MeshCodec.Wire.ProtoBytes import ProtoBytes
from convert.Formats.Fusion.MeshCodec.Wire.ProtoNumber import ProtoNumber
from convert.Formats.Fusion.MeshCodec.Wire.ProtoText import ProtoText
from convert.Formats.Fusion.MeshCodec.Wire.ReadProto import ReadProto
from convert.Formats.Fusion.MeshCodec.Wire.SelectFields import SelectFields


# the face data operation needs a distinct decoding boundary so vertex and index streams retain their intended connectivity
def ReadFaceData(Payload: bytes) -> tuple[str, tuple[FaceGroup, ...]]:
    Fields = ReadProto(Payload)
    Streams = tuple(Field for Field in Fields if Field.Number == 5)
    Groups = tuple(Field for Field in Fields if Field.Number == 6)
    if len(Streams) != 1 or len(Fields) != len(Groups) + 1:
        raise ValueError("Unsupported Fusion mesh triangle channel")
    Element, Values = SelectFields(ProtoBytes(Streams[0]), (1, 2))
    if ProtoNumber(Element) != 7:
        raise ValueError("Unsupported Fusion mesh face-group element")
    return ProtoText(Values), ReadGroups(Groups)
