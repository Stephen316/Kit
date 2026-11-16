from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


# wire node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class WireNode:
    Prefix: EntityPrefix
    NextWire: int
    FirstCoedge: int
    OwnerShell: int
    Inside: bool
