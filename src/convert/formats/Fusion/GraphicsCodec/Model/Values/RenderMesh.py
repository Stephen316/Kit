from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef


@MakeDataClass(frozen=True, slots=True)
class RenderMesh:
    Bounds: tuple[float, ...]
    FormatRef: ObjectRef | None
    Primitive: int
    VertexBuffer: ObjectRef | None
    IndexBuffer: ObjectRef | None
