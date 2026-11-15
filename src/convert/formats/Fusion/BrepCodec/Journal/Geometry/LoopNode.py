from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


# loop node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class LoopNode:
    Prefix: EntityPrefix
    NextLoop: int
    FirstCoedge: int
    OwnerFace: int
