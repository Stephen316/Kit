from convert.formats.Fusion.MeshCodec.Model.FaceGroup import FaceGroup
from convert.formats.Fusion.MeshCodec.Wire.EmitProto import EmitProto
from convert.formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField


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
