from convert.Formats.Fusion.MeshCodec.Model.MeshRegistry import MeshRegistry
from convert.Formats.Fusion.MeshCodec.Registry.ReadFaceData import ReadFaceData
from convert.Formats.Fusion.MeshCodec.Registry.ReadNormal import ReadNormal
from convert.Formats.Fusion.MeshCodec.Wire.ProtoBytes import ProtoBytes
from convert.Formats.Fusion.MeshCodec.Wire.ProtoNumber import ProtoNumber
from convert.Formats.Fusion.MeshCodec.Wire.ProtoText import ProtoText
from convert.Formats.Fusion.MeshCodec.Wire.SelectFields import SelectFields


# the registry operation needs a distinct decoding boundary so vertex and index streams retain their intended connectivity
def ReadRegistry(Payload: bytes, Order: tuple[str, ...]) -> MeshRegistry:
    Normal, Faces, Edges, Property, Count, MeshId, Vertices, Corners = SelectFields(
        Payload, (4, 5, 7, 8, 9, 12, 21, 22)
    )
    NormalId, NormalName, IndexName = ReadNormal(ProtoBytes(Normal))
    GroupName, Groups = ReadFaceData(ProtoBytes(Faces))
    EdgeName = ProtoText(SelectFields(ProtoBytes(Edges), (4,))[0])
    KeyField, IdField = SelectFields(ProtoBytes(Property), (1, 3))
    if ProtoText(KeyField) != "fusion_uuid":
        raise ValueError("Unsupported Fusion mesh named property")
    return MeshRegistry(
        ProtoText(MeshId),
        ProtoText(IdField),
        NormalId,
        ProtoNumber(Count),
        ProtoText(Vertices),
        ProtoText(Corners),
        NormalName,
        IndexName,
        EdgeName,
        GroupName,
        Groups,
        Order,
    )
