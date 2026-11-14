from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias, Union

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf


@MakeDataClass(frozen=True, slots=True)
class ChoiceValue:
    ChoiceKey: int | str
    Body: "KGrammarValue"


@MakeDataClass(frozen=True, slots=True)
class SubtypeNode:
    SubtypeName: str
    Body: "KGrammarValue"


@MakeDataClass(frozen=True, slots=True)
class LoftSubdata:
    SubdataKind: int
    RowCount: int
    ColumnCount: int
    Values: tuple[float, ...]


KGrammarValue: TypeAlias = Union[
    None,
    bool,
    int,
    float,
    str,
    tuple["KGrammarValue", ...],
    ChoiceValue,
    SubtypeNode,
    SubtypeRef,
    LoftSubdata,
    BsCurve,
    BsSurface,
    TsplineSurf,
    SubtransNode,
    TypedBase,
]

KSubtypeValue: TypeAlias = Union[SubtypeNode, SubtypeRef, TsplineSurf]

KSubtypeEntry: TypeAlias = Union[SubtypeNode, SubtypeRef, TsplineSurf, SubtransNode]
