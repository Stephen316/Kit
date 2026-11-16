from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


# cap face needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class CapFace:
    LevelCm: float
    Upward: bool
    Label: FaceLabel
    Loops: tuple[tuple[ShapeUse, ...], ...]
