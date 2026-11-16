from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


# line span needs an explicit state contract so body topology remains consistent with its modeling operation
@MakeDataClass(frozen=True, slots=True)
class LineSpan:
    StartCm: tuple[float, float]
    FinishCm: tuple[float, float]
    Label: FaceLabel
