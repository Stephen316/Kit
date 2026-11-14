from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormUse,
    FormWindow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


@MakeDataClass(frozen=True, slots=True)
class CappedCurve:
    Region: int
    Side: int
    Lower: float
    Upper: float
    Closure: int
    Links: tuple[int, ...]


@MakeDataClass(frozen=True, slots=True)
class CappedEdge:
    StartVertex: int
    EndVertex: int
    CurveIndex: int
    Convexity: str
    Label: str
    Windows: tuple[FormWindow, ...]
    Bounds: tuple[float, float] | None


@MakeDataClass(frozen=True, slots=True)
class CappedFace:
    Region: int
    Uses: tuple[FormUse, ...]
    Label: str
    DoubleSided: bool
    Contained: bool | None


@MakeDataClass(frozen=True, slots=True)
class CappedShape:
    Points: tuple[int, ...]
    Curves: tuple[CappedCurve, ...]
    Edges: tuple[CappedEdge, ...]
    Faces: tuple[CappedFace, ...]
    Regions: tuple[tuple[PatchCell, ...], ...]
    Periods: tuple[tuple[int, int], ...]
