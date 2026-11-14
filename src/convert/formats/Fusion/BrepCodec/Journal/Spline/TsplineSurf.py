from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef


@MakeDataClass(frozen=True, slots=True)
class TsplineSurf:
    Revision: int
    Cache: NubsSurface
    FitTolerance: float
    Jumps: tuple[tuple[float, ...], ...]
    Ranges: tuple[float | None, float | None, float | None, float | None]
    TypeCode: int
    Subtrans: SubtransNode | SubtypeRef
    FaceIndex: int
