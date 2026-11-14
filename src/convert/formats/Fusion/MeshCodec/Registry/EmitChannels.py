from convert.formats.Fusion.MeshCodec.Model.MeshRegistry import MeshRegistry
from convert.formats.Fusion.MeshCodec.Registry.EmitGroup import EmitGroup
from convert.formats.Fusion.MeshCodec.Wire.EmitProto import EmitProto
from convert.formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField


def EmitChannels(Value: MeshRegistry) -> tuple[ProtoField, ProtoField]:
    Normal = EmitProto(
        (
            ProtoField(3, Value.NormalId.encode("utf-8")),
            ProtoField(
                5,
                EmitProto(
                    (
                        ProtoField(1, 5),
                        ProtoField(2, Value.NormalStream.encode("utf-8")),
                        ProtoField(3, Value.OverrideStream.encode("utf-8")),
                    )
                ),
            ),
        )
    )
    Groups = EmitProto(
        (
            ProtoField(
                5,
                EmitProto(
                    (
                        ProtoField(1, 7),
                        ProtoField(2, Value.GroupStream.encode("utf-8")),
                    )
                ),
            ),
            *(EmitGroup(Group) for Group in Value.Groups),
        )
    )
    return ProtoField(4, Normal), ProtoField(5, Groups)
