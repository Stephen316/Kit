from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class LumpNode:
    Prefix: EntityPrefix
    NextLump: int
    FirstShell: int
    OwnerBody: int
