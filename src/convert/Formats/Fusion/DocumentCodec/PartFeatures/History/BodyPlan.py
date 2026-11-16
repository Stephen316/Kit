from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge


# body plan needs an explicit state contract so feature parameters remain connected to the resulting geometry
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
