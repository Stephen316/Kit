from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexData import VertexData
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef


@MakeDataClass(frozen=True, slots=True)
class SimpleMesh:
    Bounds: tuple[float, ...]
    Primitive: int
    VertexBuffer: VertexData | None
    IndexBuffer: ObjectRef | None
    IsPlanar: bool
