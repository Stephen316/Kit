from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class BodyNode:
    Prefix: EntityPrefix
    FirstLump: int
    TransformRef: int = -1
