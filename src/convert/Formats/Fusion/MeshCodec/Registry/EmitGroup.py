from convert.Formats.Fusion.MeshCodec.Model.FaceGroup import FaceGroup
from convert.Formats.Fusion.MeshCodec.Wire.EmitProto import EmitProto
from convert.Formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField


# the group operation needs a consistent construction rule so vertex and index streams retain their intended connectivity
def EmitGroup(Group: FaceGroup) -> ProtoField:
    return ProtoField(
        6,
        EmitProto(
            (
                ProtoField(1, Group.GroupKey),
                ProtoField(2, Group.GroupId.encode("utf-8")),
            )
        ),
    )
