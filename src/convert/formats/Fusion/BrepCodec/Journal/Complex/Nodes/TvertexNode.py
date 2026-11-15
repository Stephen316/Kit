from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode


# tvertex node needs an explicit state contract so nested spline and surface records retain their relationships
@MakeDataClass(frozen=True, slots=True)
class TvertexNode:
    Base: VertexNode
    Sentinel: float
    Tolerance: float
    SavedTolerance: float
    Stamp: int
