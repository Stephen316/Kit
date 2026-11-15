from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Planar.BoundaryUse import BoundaryUse


# face boundary needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class FaceBoundary:
    FaceRef: int
    Surface: PlaneNode
    Reversed: bool
    BoundaryUses: tuple[BoundaryUse, ...]
