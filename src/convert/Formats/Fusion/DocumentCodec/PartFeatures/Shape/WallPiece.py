from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan


# wall piece needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class WallPiece:
    Span: KPlaneSpan
    LowerCm: float
    UpperCm: float
    Joints: tuple[tuple[float, float], tuple[float, float]]
