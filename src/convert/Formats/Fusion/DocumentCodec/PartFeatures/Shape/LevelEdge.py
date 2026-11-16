from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan


# level edge needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class LevelEdge:
    Span: KPlaneSpan
    LevelCm: float
