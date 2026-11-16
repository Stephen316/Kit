from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.Values.VertexData import VertexData
from convert.Formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef


# simple mesh needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class SimpleMesh:
    Bounds: tuple[float, ...]
    Primitive: int
    VertexBuffer: VertexData | None
    IndexBuffer: ObjectRef | None
    IsPlanar: bool
