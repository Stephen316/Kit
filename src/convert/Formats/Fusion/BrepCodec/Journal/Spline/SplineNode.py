from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KSubtypeValue,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


# spline node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class SplineNode:
    Prefix: EntityPrefix
    Reversed: bool
    Surface: KSubtypeValue
    ULower: float | None
    UUpper: float | None
    VLower: float | None
    VUpper: float | None
