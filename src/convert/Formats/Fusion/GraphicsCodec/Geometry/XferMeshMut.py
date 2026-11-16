from __future__ import annotations
from typing import TYPE_CHECKING
from convert.Formats.Fusion.GraphicsCodec.Geometry.XferVerticesMut import (
    XferVerticesMut,
)

from convert.Formats.Fusion.GraphicsCodec.Model.Values.SimpleMesh import SimpleMesh
from convert.Formats.Fusion.GraphicsCodec.Model.Values.IndexData import IndexData

if TYPE_CHECKING:
    from convert.Formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


# transfer mesh needs an explicit validity boundary so display geometry retains its entity and scene relationships
def XferMeshMut(State: SceneCodec, Value: SimpleMesh | None) -> SimpleMesh:
    Bounds = State.Vector(Value.Bounds if Value else None, 6)
    Primitive = State.Integer(Value.Primitive if Value else None, "<i")
    if Primitive not in (2, 3, 4, 5):
        raise ValueError("Unsupported graphics primitive topology")
    VertexBuffer = (
        XferVerticesMut(State, Value.VertexBuffer if Value else None)
        if State.IsFlag(Value is not None and Value.VertexBuffer is not None)
        else None
    )
    IndexBuffer = State.LinkedObject(
        "AIndexBuffer", Value.IndexBuffer if Value else None
    )
    IsPlanar = State.IsFlag(Value.IsPlanar if Value else None)
    if IndexBuffer is not None:
        Indices = State.ObjectValues[IndexBuffer]
        if (
            not isinstance(Indices, IndexData)
            or VertexBuffer is None
            or any(Index >= len(VertexBuffer.Values) for Index in Indices.Values)
        ):
            raise ValueError("Graphics indices do not address their vertex buffer")
    return SimpleMesh(Bounds, Primitive, VertexBuffer, IndexBuffer, IsPlanar)
