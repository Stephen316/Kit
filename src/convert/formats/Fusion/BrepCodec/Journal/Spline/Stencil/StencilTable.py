from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilCurve import (
    StencilCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilFace import (
    StencilFace,
)


@MakeDataClass(frozen=True, slots=True)
class StencilTable:
    GripCount: int
    Rows: tuple[tuple[tuple[int, float], ...], ...]
    Faces: tuple[StencilFace, ...]
    Curves: tuple[StencilCurve, ...]
    Points: tuple[int, ...]
