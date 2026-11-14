from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class FaceNode:
    Prefix: EntityPrefix
    NextFace: int
    FirstLoop: int
    OwnerShell: int
    Surface: int
    Reversed: bool
    DoubleSided: bool
    Contained: bool | None
