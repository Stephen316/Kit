from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeFace import FreeFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel

KShapeFace: TypeAlias = WallFace | CapFace | FreeFace


@MakeDataClass(frozen=True, slots=True)
class ShapeBody:
    Faces: tuple[KShapeFace, ...]
    BodyLabel: FaceLabel
    SketchCurves: tuple[tuple[FaceLabel, int], ...]
    BaseLevelCm: float
    EdgeTags: tuple[tuple[FaceLabel, float, FaceLabel], ...] = ()
    Tracks: tuple[tuple[FaceLabel, int], ...] = ()
    Ordinal: int = 1
