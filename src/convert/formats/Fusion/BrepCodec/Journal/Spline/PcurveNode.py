from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KSubtypeValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix


@MakeDataClass(frozen=True, slots=True)
class PcurveNode:
    Prefix: EntityPrefix
    Reversed: bool
    Curve: KSubtypeValue | None
    OffsetU: float
    OffsetV: float
    Form: int = 0
    CurveRef: int = -1
