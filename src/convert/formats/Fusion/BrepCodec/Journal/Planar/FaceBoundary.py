from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Planar.BoundaryUse import BoundaryUse


@MakeDataClass(frozen=True, slots=True)
class FaceBoundary:
    FaceRef: int
    Surface: PlaneNode
    Reversed: bool
    BoundaryUses: tuple[BoundaryUse, ...]
