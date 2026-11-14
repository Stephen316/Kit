from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel


@MakeDataClass(frozen=True, slots=True)
class LineSpan:
    StartCm: tuple[float, float]
    FinishCm: tuple[float, float]
    Label: FaceLabel
