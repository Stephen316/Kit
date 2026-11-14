from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KSubtypeValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class SplineNode:
    Prefix: EntityPrefix
    Reversed: bool
    Surface: KSubtypeValue
    ULower: float | None
    UUpper: float | None
    VLower: float | None
    VUpper: float | None
