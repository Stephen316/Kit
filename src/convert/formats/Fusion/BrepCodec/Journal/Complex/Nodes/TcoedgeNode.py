from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode


@MakeDataClass(frozen=True, slots=True)
class TcoedgeNode:
    Base: CoedgeNode
    RangeLower: float
    RangeUpper: float
    CurveRef: int
    CurveForm: int
    Curve: KGrammarValue
    Stamp: int
