from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


@MakeDataClass(frozen=True, slots=True)
class FormWindow:
    Face: int
    ULow: float
    UHigh: float
    VLow: float
    VHigh: float


@MakeDataClass(frozen=True, slots=True)
class FormSurface:
    Cache: NubsSurface
    Jumps: tuple[tuple[float, ...], ...]
    Region: int


@MakeDataClass(frozen=True, slots=True)
class FormEdge:
    StartVertex: int
    EndVertex: int
    Curve: BsCurve
    Jumps: tuple[tuple[float, ...], ...]
    Convexity: str = "unknown"
    Label: str = ""
    Windows: tuple[FormWindow, ...] = ()
    Bounds: tuple[float, float] | None = None


@MakeDataClass(frozen=True, slots=True)
class FormUse:
    EdgeIndex: int
    Reversed: bool
    Pcurve: BsCurve
    Fit: float = 0.0


@MakeDataClass(frozen=True, slots=True)
class FormFace:
    Surface: FormSurface
    Uses: tuple[FormUse, ...]
    Label: str = ""
    DoubleSided: bool = False
    Contained: bool | None = None


@MakeDataClass(frozen=True, slots=True)
class FormBody:
    PointsCm: tuple[KJournalVector, ...]
    Edges: tuple[FormEdge, ...]
    Faces: tuple[FormFace, ...]
    Regions: tuple[tuple[PatchCell, ...], ...]
