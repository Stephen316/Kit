from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class CoedgeNode:
    Prefix: EntityPrefix
    NextCoedge: int
    PriorCoedge: int
    Partner: int
    EdgeRef: int
    Reversed: bool
    OwnerLoop: int
    Pcurve: int = -1
