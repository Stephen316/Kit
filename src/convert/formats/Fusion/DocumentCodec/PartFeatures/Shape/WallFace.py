from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan


# wall face needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class WallFace:
    Span: KPlaneSpan
    LowerCm: float
    UpperCm: float
    Loops: tuple[tuple[ShapeUse, ...], ...]
    RoofSpan: KPlaneSpan | None = None
