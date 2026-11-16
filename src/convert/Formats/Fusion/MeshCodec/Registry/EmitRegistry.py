from convert.Formats.Fusion.MeshCodec.Model.MeshRegistry import MeshRegistry
from convert.Formats.Fusion.MeshCodec.Registry.EmitChannels import EmitChannels
from convert.Formats.Fusion.MeshCodec.Wire.EmitProto import EmitProto
from convert.Formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField


# the registry operation needs a consistent construction rule so vertex and index streams retain their intended connectivity
def EmitRegistry(Value: MeshRegistry) -> bytes:
    return EmitProto(
        (
            *EmitChannels(Value),
            ProtoField(
                7, EmitProto((ProtoField(4, Value.EdgeStream.encode("utf-8")),))
            ),
            ProtoField(
                8,
                EmitProto(
                    (
                        ProtoField(1, b"fusion_uuid"),
                        ProtoField(3, Value.FusionId.encode("utf-8")),
                    )
                ),
            ),
            ProtoField(9, Value.FaceGroupCount),
            ProtoField(12, Value.MeshId.encode("utf-8")),
            ProtoField(21, Value.VertexStream.encode("utf-8")),
            ProtoField(22, Value.CornerStream.encode("utf-8")),
        )
    )
