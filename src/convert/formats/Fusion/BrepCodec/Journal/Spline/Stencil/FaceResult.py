from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface


# face result needs an explicit state contract so control cage contributions retain their intended weights
@MakeDataClass(frozen=True, slots=True)
class FaceResult:
    FaceIndex: int
    Surface: NubsSurface
    Jumps: tuple[tuple[float, ...], ...]
