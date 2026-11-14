from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan


@MakeDataClass(frozen=True, slots=True)
class WallFace:
    Span: KPlaneSpan
    LowerCm: float
    UpperCm: float
    Loops: tuple[tuple[ShapeUse, ...], ...]
    RoofSpan: KPlaneSpan | None = None
