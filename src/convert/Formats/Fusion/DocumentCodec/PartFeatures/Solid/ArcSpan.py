from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


# arc span needs an explicit state contract so body topology remains consistent with its modeling operation
@MakeDataClass(frozen=True, slots=True)
class ArcSpan:
    CenterCm: tuple[float, float]
    RadiusCm: float
    StartAngle: float
    SweepAngle: float
    Label: FaceLabel
