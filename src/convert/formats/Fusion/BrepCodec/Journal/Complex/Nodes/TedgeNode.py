from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode


# tedge node needs an explicit state contract so nested spline and surface records retain their relationships
@MakeDataClass(frozen=True, slots=True)
class TedgeNode:
    Base: EdgeNode
    Tolerance: float
    SaveVersion: int
    Stamp: int
