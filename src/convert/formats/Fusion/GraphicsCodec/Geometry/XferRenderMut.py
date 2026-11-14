from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Model.Values.RenderMesh import RenderMesh
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexData import VertexData
from convert.formats.Fusion.GraphicsCodec.Model.Values.IndexData import IndexData

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferRenderMut(State: SceneCodec, Value: RenderMesh | None) -> RenderMesh:
    Bounds = State.Vector(Value.Bounds if Value else None, 6)
    FormatRef = State.LinkedObject("VertexFormat", Value.FormatRef if Value else None)
    Primitive = State.Integer(Value.Primitive if Value else None, "<i")
    if Primitive not in (2, 3, 4):
        raise ValueError(f"Unsupported graphics primitive topology: {Primitive}")
    VertexBuffer = State.LinkedObject(
        "VertexBuffer", Value.VertexBuffer if Value else None
    )
    IndexFlag = State.Integer(
        int(Value.IndexBuffer is not None) if Value else None, "<i"
    )
    if IndexFlag not in (0, 1):
        raise ValueError("Unsupported graphics index save flag")
    IndexBuffer = (
        State.LinkedObject("AIndexBuffer", Value.IndexBuffer if Value else None)
        if IndexFlag
        else None
    )
    if IndexFlag and IndexBuffer is None:
        raise ValueError("Missing saved graphics index buffer")
    Vertices = State.ObjectValues[VertexBuffer] if VertexBuffer else None
    if Vertices is not None and (
        not isinstance(Vertices, VertexData) or Vertices.FormatRef != FormatRef
    ):
        raise ValueError("Graphics mesh and vertex buffer formats differ")
    if IndexBuffer is not None:
        Indices = State.ObjectValues[IndexBuffer]
        if (
            not isinstance(Indices, IndexData)
            or not isinstance(Vertices, VertexData)
            or any(Index >= len(Vertices.Values) for Index in Indices.Values)
        ):
            raise ValueError("Graphics indices do not address their vertex buffer")
    return RenderMesh(Bounds, FormatRef, Primitive, VertexBuffer, IndexBuffer)
