from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot


# stencil face needs an explicit state contract so control cage contributions retain their intended weights
@MakeDataClass(frozen=True, slots=True)
class StencilFace:
    FaceIndex: int
    KnotsU: tuple[SplineKnot, ...]
    KnotsV: tuple[SplineKnot, ...]
    Poles: tuple[int, ...]
