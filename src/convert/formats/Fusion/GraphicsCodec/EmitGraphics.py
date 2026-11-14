from typing import cast as CastValue
from struct import error as StructError
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsData import GraphicsData
from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec
from convert.formats.Fusion.GraphicsCodec.Wire.ObjectValueMut import ObjectValueMut
from convert.formats.Fusion.GraphicsCodec.Fields.XferOverrideMut import XferOverrideMut
from convert.formats.Fusion.GraphicsCodec.Worlds.XferWorldMut import XferWorldMut


def EmitGraphics(Value: GraphicScene) -> GraphicsData:
    if not isinstance(CastValue(object, Value), GraphicScene):
        raise ValueError("Expected a typed Fusion graphics scene")
    try:
        State = SceneCodec(None, (), (), Value, ObjectValueMut, XferOverrideMut)
        _ = XferWorldMut(State, Value.RootWorld, True)
        _ = State.Finalize()
        Streams = State.MeshData.Finalize()
        FusionStreams = State.FusionData.Finalize()
        return GraphicsData(bytes(State.Output), Streams, FusionStreams)
    except (StructError, UnicodeError, OverflowError) as Error:
        raise ValueError("Invalid Fusion graphics model field") from Error
