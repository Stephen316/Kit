from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


# coedge node needs an explicit state contract so topology changes retain their native revision relationships
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
