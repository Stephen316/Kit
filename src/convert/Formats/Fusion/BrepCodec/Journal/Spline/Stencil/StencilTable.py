from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilCurve import (
    StencilCurve,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilFace import (
    StencilFace,
)


# stencil table needs an explicit state contract so control cage contributions retain their intended weights
@MakeDataClass(frozen=True, slots=True)
class StencilTable:
    GripCount: int
    Rows: tuple[tuple[tuple[int, float], ...], ...]
    Faces: tuple[StencilFace, ...]
    Curves: tuple[StencilCurve, ...]
    Points: tuple[int, ...]
