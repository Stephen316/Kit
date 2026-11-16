from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.ContainerCodec.IsGraphicPath import IsGraphicPath
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)
from convert.Formats.Fusion.GraphicsCodec.ReadGraphics import ReadGraphics


# the scene parts operation needs a distinct decoding boundary so supporting records retain their owning document relationships
def ReadSceneParts(Values: tuple[ContainerPart, ...]) -> GraphicScene | None:
    Parts = tuple(Entry for Entry in Values if Entry.Name.startswith("OGS.BlobFolder/"))
    if not Parts:
        return None
    Prefix = "OGS.BlobFolder/OGS/DefaultScene/"
    if any(not IsGraphicPath(Entry.Name) for Entry in Parts):
        raise ValueError("Unsupported Fusion graphics member path")
    WorldParts = tuple(Entry for Entry in Parts if Entry.Name == Prefix + "world")
    if len(WorldParts) != 1:
        raise ValueError("Graphics members require exactly one world")
    Streams = tuple(
        GraphicsStream(int(Entry.Name[-3:]), Entry.Payload)
        for Entry in Parts
        if Entry.Name.startswith(Prefix + "stream_mesh_")
    )
    FusionStreams = tuple(
        GraphicsStream(int(Entry.Name[-3:]), Entry.Payload)
        for Entry in Parts
        if Entry.Name.startswith(Prefix + "Fusion_mesh_")
    )
    return ReadGraphics(WorldParts[0].Payload, Streams, FusionStreams)
