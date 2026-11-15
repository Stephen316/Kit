from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    KSpaceVector,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


# edge round needs an explicit state contract so edge and face relationships survive parametric feature construction
@MakeDataClass(frozen=True, slots=True)
class EdgeRound:
    PointsCm: tuple[KSpaceVector, ...]
    CapCm: float
    WallCm: float
    Rounded: bool
    Operation: int
    Blends: tuple[FaceLabel, ...] = ()
