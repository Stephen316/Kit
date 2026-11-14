from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class LoopNode:
    Prefix: EntityPrefix
    NextLoop: int
    FirstCoedge: int
    OwnerFace: int
