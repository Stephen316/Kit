from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


@MakeDataClass(frozen=True, slots=True)
class CapFace:
    LevelCm: float
    Upward: bool
    Label: FaceLabel
    Loops: tuple[tuple[ShapeUse, ...], ...]
