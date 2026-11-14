from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge


@MakeDataClass(frozen=True, slots=True)
class BodyPlan:
    Body: ShapeBody
    Ordinal: int
    Edges: tuple[KShapeEdge, ...]
    EdgeOwners: dict[KShapeEdge, tuple[object, ...]]
    Partners: dict[tuple[object, ...], tuple[object, ...]]
    Vertices: tuple[tuple[float, float, float], ...]
    VertexOwners: dict[tuple[float, float, float], tuple[KShapeEdge, int]]
    FaceTags: dict[tuple[object, ...], int]
    BodyTag: int
    UnixMicros: float
