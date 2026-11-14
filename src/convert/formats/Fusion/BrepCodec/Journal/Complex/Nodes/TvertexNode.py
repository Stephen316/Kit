from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode


@MakeDataClass(frozen=True, slots=True)
class TvertexNode:
    Base: VertexNode
    Sentinel: float
    Tolerance: float
    SavedTolerance: float
    Stamp: int
