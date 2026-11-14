from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot


@MakeDataClass(frozen=True, slots=True)
class StencilFace:
    FaceIndex: int
    KnotsU: tuple[SplineKnot, ...]
    KnotsV: tuple[SplineKnot, ...]
    Poles: tuple[int, ...]
