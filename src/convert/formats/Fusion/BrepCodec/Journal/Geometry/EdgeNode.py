from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class EdgeNode:
    Prefix: EntityPrefix
    StartVertex: int
    StartParam: float
    EndVertex: int
    EndParam: float
    OwnerCoedge: int
    CurveRef: int
    Reversed: bool
    Convexity: str
