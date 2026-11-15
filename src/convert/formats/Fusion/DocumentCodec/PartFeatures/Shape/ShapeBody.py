from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeFace import FreeFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel

# the shape face variants need one shared contract so parametric feature reconstruction cannot omit a supported value shape
KShapeFace: TypeAlias = WallFace | CapFace | FreeFace


# shape body needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class ShapeBody:
    Faces: tuple[KShapeFace, ...]
    BodyLabel: FaceLabel
    SketchCurves: tuple[tuple[FaceLabel, int], ...]
    BaseLevelCm: float
    EdgeTags: tuple[tuple[FaceLabel, float, FaceLabel], ...] = ()
    Tracks: tuple[tuple[FaceLabel, int], ...] = ()
    Ordinal: int = 1
