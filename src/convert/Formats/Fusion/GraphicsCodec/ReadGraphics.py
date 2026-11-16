from struct import error as StructError
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)
from convert.Formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec
from convert.Formats.Fusion.GraphicsCodec.Wire.ObjectValueMut import ObjectValueMut
from convert.Formats.Fusion.GraphicsCodec.Fields.XferOverrideMut import XferOverrideMut
from convert.Formats.Fusion.GraphicsCodec.Worlds.XferWorldMut import XferWorldMut


# the graphics operation needs a distinct decoding boundary so display geometry retains its entity and scene relationships
def ReadGraphics(
    WorldData: bytes,
    MeshStreams: tuple[GraphicsStream, ...],
    FusionStreams: tuple[GraphicsStream, ...],
) -> GraphicScene:
    if type(WorldData) is not bytes or len(WorldData) > 67108864:
        raise ValueError("Invalid graphics world input")
    try:
        State = SceneCodec(
            WorldData,
            MeshStreams,
            FusionStreams,
            None,
            ObjectValueMut,
            XferOverrideMut,
        )
        RootWorld = XferWorldMut(State, None, True)
        Objects = State.Finalize()
        _ = State.MeshData.Finalize()
        _ = State.FusionData.Finalize()
        if State.Globals is None:
            raise ValueError("Missing graphics serializer versions")
        return GraphicScene(
            State.Globals,
            RootWorld,
            Objects,
            State.MeshData.SlackValues(),
            State.FusionData.SlackValues(),
        )
    except (StructError, UnicodeError, OverflowError) as Error:
        raise ValueError("Invalid Fusion graphics wire field") from Error
