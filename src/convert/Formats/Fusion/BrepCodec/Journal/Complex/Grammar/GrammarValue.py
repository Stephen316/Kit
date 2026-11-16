from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias, Union

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.Formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf


# choice value needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class ChoiceValue:
    ChoiceKey: int | str
    Body: "KGrammarValue"


# subtype node needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class SubtypeNode:
    SubtypeName: str
    Body: "KGrammarValue"


# loft subdata needs an explicit state contract so nested geometry retains unambiguous record boundaries
@MakeDataClass(frozen=True, slots=True)
class LoftSubdata:
    SubdataKind: int
    RowCount: int
    ColumnCount: int
    Values: tuple[float, ...]


# the grammar value shape must stay shared so journal grammar decoding uses one contract for compatible values
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

# the subtype value shape must stay shared so journal grammar decoding uses one contract for compatible values
KSubtypeValue: TypeAlias = Union[SubtypeNode, SubtypeRef, TsplineSurf]

# the subtype entry shape must stay shared so journal grammar decoding uses one contract for compatible values
KSubtypeEntry: TypeAlias = Union[SubtypeNode, SubtypeRef, TsplineSurf, SubtransNode]
