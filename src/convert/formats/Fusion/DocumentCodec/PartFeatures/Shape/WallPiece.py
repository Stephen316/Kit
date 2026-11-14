from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan


@MakeDataClass(frozen=True, slots=True)
class WallPiece:
    Span: KPlaneSpan
    LowerCm: float
    UpperCm: float
    Joints: tuple[tuple[float, float], tuple[float, float]]
