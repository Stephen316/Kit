from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface


@MakeDataClass(frozen=True, slots=True)
class FaceResult:
    FaceIndex: int
    Surface: NubsSurface
    Jumps: tuple[tuple[float, ...], ...]
