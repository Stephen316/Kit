from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


# lump node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class LumpNode:
    Prefix: EntityPrefix
    NextLump: int
    FirstShell: int
    OwnerBody: int
