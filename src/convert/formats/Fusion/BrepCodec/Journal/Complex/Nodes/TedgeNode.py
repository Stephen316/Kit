from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode


@MakeDataClass(frozen=True, slots=True)
class TedgeNode:
    Base: EdgeNode
    Tolerance: float
    SaveVersion: int
    Stamp: int
