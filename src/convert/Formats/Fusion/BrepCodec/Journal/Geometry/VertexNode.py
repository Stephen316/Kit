from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


# vertex node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class VertexNode:
    Prefix: EntityPrefix
    OwnerEdge: int
    EdgeIndex: int
    PointRef: int
