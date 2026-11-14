from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class VertexNode:
    Prefix: EntityPrefix
    OwnerEdge: int
    EdgeIndex: int
    PointRef: int
