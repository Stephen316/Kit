from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


@MakeDataClass(frozen=True, slots=True)
class ArcSpan:
    CenterCm: tuple[float, float]
    RadiusCm: float
    StartAngle: float
    SweepAngle: float
    Label: FaceLabel
