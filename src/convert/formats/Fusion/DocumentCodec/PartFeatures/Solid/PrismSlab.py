from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneLoop


@MakeDataClass(frozen=True, slots=True)
class PrismSlab:
    LowerCm: float
    UpperCm: float
    Loops: tuple[KPlaneLoop, ...]
    FloorLabel: FaceLabel
    RoofLabel: FaceLabel
    RoofLoops: tuple[KPlaneLoop, ...] = ()
