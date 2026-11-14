from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan


@MakeDataClass(frozen=True, slots=True)
class LevelEdge:
    Span: KPlaneSpan
    LevelCm: float
