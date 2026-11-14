from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class WireNode:
    Prefix: EntityPrefix
    NextWire: int
    FirstCoedge: int
    OwnerShell: int
    Inside: bool
