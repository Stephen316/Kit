from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.FaceResult import (
    FaceResult,
)


@MakeDataClass(frozen=True, slots=True)
class CageResult:
    Faces: tuple[FaceResult, ...]
    Curves: tuple[BsCurve, ...]
    CurveJumps: tuple[tuple[tuple[float, ...], ...], ...]
    Points: tuple[KJournalVector, ...]
