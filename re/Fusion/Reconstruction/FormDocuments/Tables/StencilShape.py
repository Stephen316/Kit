"""Research copy of the retired per-layout Form tables. Nothing in src/ loads this folder."""
from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormUse,
    FormWindow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


@MakeDataClass(frozen=True, slots=True)
class ShapeEdge:
    StartVertex: int
    EndVertex: int
    CurveIndex: int
    Convexity: str
    Label: str
    Windows: tuple[FormWindow, ...]
    Bounds: tuple[float, float] | None


@MakeDataClass(frozen=True, slots=True)
class ShapeFace:
    FaceIndex: int
    Uses: tuple[FormUse, ...]
    Label: str
    DoubleSided: bool
    Contained: bool | None


@MakeDataClass(frozen=True, slots=True)
class StencilShape:
    Label: str
    LayoutKey: str
    Points: tuple[int, ...]
    Edges: tuple[ShapeEdge, ...]
    Faces: tuple[ShapeFace, ...]
    Regions: tuple[tuple[PatchCell, ...], ...]
