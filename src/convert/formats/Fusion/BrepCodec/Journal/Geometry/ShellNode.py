from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class ShellNode:
    Prefix: EntityPrefix
    NextShell: int
    FirstFace: int
    OwnerLump: int
    FirstWire: int = -1
