from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode


# tcoedge node needs an explicit state contract so nested spline and surface records retain their relationships
@MakeDataClass(frozen=True, slots=True)
class TcoedgeNode:
    Base: CoedgeNode
    RangeLower: float
    RangeUpper: float
    CurveRef: int
    CurveForm: int
    Curve: KGrammarValue
    Stamp: int
