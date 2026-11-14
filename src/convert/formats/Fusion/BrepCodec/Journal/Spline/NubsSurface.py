from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot


@MakeDataClass(frozen=True, slots=True)
class NubsSurface:
    DegreeU: int
    DegreeV: int
    ClosureU: int
    ClosureV: int
    SingularU: int
    SingularV: int
    KnotsU: tuple[SplineKnot, ...]
    KnotsV: tuple[SplineKnot, ...]
    Points: tuple[KJournalVector, ...]
    Weights: tuple[float, ...] = ()
    Form: str = ""
