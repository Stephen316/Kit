from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.Formats.Fusion.GraphicsCodec.EmitGraphics import EmitGraphics


# the scene parts operation needs a consistent construction rule so supporting records retain their owning document relationships
def EmitSceneParts(Value: GraphicScene | None) -> tuple[ContainerPart, ...]:
    if Value is None:
        return ()
    DataValue = EmitGraphics(Value)
    Prefix = "OGS.BlobFolder/OGS/DefaultScene/"
    return (
        (ContainerPart(Prefix + "world", DataValue.WorldData),)
        + tuple(
            ContainerPart(
                Prefix + f"stream_mesh_{Entry.StreamIndex:03d}", Entry.Payload
            )
            for Entry in DataValue.MeshStreams
        )
        + tuple(
            ContainerPart(
                Prefix + f"Fusion_mesh_{Entry.StreamIndex:03d}", Entry.Payload
            )
            for Entry in DataValue.FusionStreams
        )
    )
