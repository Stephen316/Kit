from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.FaceResult import (
    FaceResult,
)


# cage result needs an explicit state contract so control cage contributions retain their intended weights
@MakeDataClass(frozen=True, slots=True)
class CageResult:
    Faces: tuple[FaceResult, ...]
    Curves: tuple[BsCurve, ...]
    CurveJumps: tuple[tuple[tuple[float, ...], ...], ...]
    Points: tuple[KJournalVector, ...]
