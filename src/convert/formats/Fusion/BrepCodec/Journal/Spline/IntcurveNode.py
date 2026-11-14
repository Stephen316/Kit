from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KSubtypeValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class IntcurveNode:
    Prefix: EntityPrefix
    Reversed: bool
    Curve: KSubtypeValue
    Lower: float | None
    Upper: float | None
