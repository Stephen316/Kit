from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


# form window needs an explicit state contract so surface geometry retains the control cage shape
@MakeDataClass(frozen=True, slots=True)
class FormWindow:
    Face: int
    ULow: float
    UHigh: float
    VLow: float
    VHigh: float


# form surface needs an explicit state contract so surface geometry retains the control cage shape
@MakeDataClass(frozen=True, slots=True)
class FormSurface:
    Cache: NubsSurface
    Jumps: tuple[tuple[float, ...], ...]
    Region: int


# form edge needs an explicit state contract so surface geometry retains the control cage shape
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


# form use needs an explicit state contract so surface geometry retains the control cage shape
@MakeDataClass(frozen=True, slots=True)
class FormUse:
    EdgeIndex: int
    Reversed: bool
    Pcurve: BsCurve
    Fit: float = 0.0


# form face needs an explicit state contract so surface geometry retains the control cage shape
@MakeDataClass(frozen=True, slots=True)
class FormFace:
    Surface: FormSurface
    Uses: tuple[FormUse, ...]
    Label: str = ""
    DoubleSided: bool = False
    Contained: bool | None = None


# form body needs an explicit state contract so surface geometry retains the control cage shape
@MakeDataClass(frozen=True, slots=True)
class FormBody:
    PointsCm: tuple[KJournalVector, ...]
    Edges: tuple[FormEdge, ...]
    Faces: tuple[FormFace, ...]
    Regions: tuple[tuple[PatchCell, ...], ...]
