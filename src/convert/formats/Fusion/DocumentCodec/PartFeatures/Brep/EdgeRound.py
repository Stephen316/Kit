from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    KSpaceVector,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


@MakeDataClass(frozen=True, slots=True)
class EdgeRound:
    PointsCm: tuple[KSpaceVector, ...]
    CapCm: float
    WallCm: float
    Rounded: bool
    Operation: int
    Blends: tuple[FaceLabel, ...] = ()
