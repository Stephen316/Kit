from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormUse,
    FormWindow,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


# capped curve needs an explicit state contract so cap boundaries remain connected to the surrounding surface
@MakeDataClass(frozen=True, slots=True)
class CappedCurve:
    Region: int
    Side: int
    Lower: float
    Upper: float
    Closure: int
    Links: tuple[int, ...]


# capped edge needs an explicit state contract so cap boundaries remain connected to the surrounding surface
@MakeDataClass(frozen=True, slots=True)
class CappedEdge:
    StartVertex: int
    EndVertex: int
    CurveIndex: int
    Convexity: str
    Label: str
    Windows: tuple[FormWindow, ...]
    Bounds: tuple[float, float] | None


# capped face needs an explicit state contract so cap boundaries remain connected to the surrounding surface
@MakeDataClass(frozen=True, slots=True)
class CappedFace:
    Region: int
    Uses: tuple[FormUse, ...]
    Label: str
    DoubleSided: bool
    Contained: bool | None


# capped shape needs an explicit state contract so cap boundaries remain connected to the surrounding surface
@MakeDataClass(frozen=True, slots=True)
class CappedShape:
    Points: tuple[int, ...]
    Curves: tuple[CappedCurve, ...]
    Edges: tuple[CappedEdge, ...]
    Faces: tuple[CappedFace, ...]
    Regions: tuple[tuple[PatchCell, ...], ...]
    Periods: tuple[tuple[int, int], ...]
