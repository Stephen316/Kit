from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


# shell node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class ShellNode:
    Prefix: EntityPrefix
    NextShell: int
    FirstFace: int
    OwnerLump: int
    FirstWire: int = -1
