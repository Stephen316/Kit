from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.Formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell


# grid result needs an explicit state contract so surface geometry retains the control cage shape
@MakeDataClass(frozen=True, slots=True)
class GridResult:
    Surface: NubsSurface
    Patches: tuple[PatchCell, ...]
    Bounds: tuple[BsCurve, BsCurve, BsCurve, BsCurve]
    Corners: tuple[KJournalVector, KJournalVector, KJournalVector, KJournalVector]
    SurfaceJumps: tuple[tuple[float, ...], ...]
    BoundJumps: tuple[tuple[float, ...], ...]
