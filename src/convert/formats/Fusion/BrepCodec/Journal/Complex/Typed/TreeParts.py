from typing import TypeAlias, TypeVar

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
    LoftSubdata,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface

KTriple: TypeAlias = tuple[float, float, float]

KRange: TypeAlias = tuple[float | None, float | None]

KBreaks: TypeAlias = tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]

KRecordKind = TypeVar("KRecordKind")


def NeedRecord(Value: object, RecordKind: type[KRecordKind]) -> KRecordKind:
    if not isinstance(Value, RecordKind):
        raise ValueError("Fusion typed subtype body has the wrong record class")
    return Value


def NeedItems(Value: KGrammarValue, Length: int | None) -> tuple[KGrammarValue, ...]:
    if type(Value) is not tuple or (Length is not None and len(Value) != Length):
        raise ValueError("Fusion typed subtype field disagrees with its grammar")
    return Value


def NeedReal(Value: KGrammarValue) -> float:
    if type(Value) is not float:
        raise ValueError("Fusion typed subtype field requires a real")
    return Value


def NeedWhole(Value: KGrammarValue) -> int:
    if type(Value) is not int:
        raise ValueError("Fusion typed subtype field requires an integer")
    return Value


def IsFlagSet(Value: KGrammarValue) -> bool:
    if type(Value) is not bool:
        raise ValueError("Fusion typed subtype field requires a logical")
    return Value


def NeedText(Value: KGrammarValue) -> str:
    if type(Value) is not str:
        raise ValueError("Fusion typed subtype field requires text")
    return Value


def NeedBound(Value: KGrammarValue) -> float | None:
    return None if Value is None else NeedReal(Value)


def NeedRange(Value: KGrammarValue) -> KRange:
    LowBound, HighBound = NeedItems(Value, 2)
    return NeedBound(LowBound), NeedBound(HighBound)


def NeedTriple(Value: KGrammarValue) -> KTriple:
    First, Second, Third = NeedItems(Value, 3)
    return NeedReal(First), NeedReal(Second), NeedReal(Third)


def NeedReals(Value: KGrammarValue) -> tuple[float, ...]:
    return tuple(NeedReal(Element) for Element in NeedItems(Value, None))


def NeedBreaks(Values: tuple[KGrammarValue, ...]) -> KBreaks:
    if len(Values) != 3:
        raise ValueError("Fusion discontinuity record requires three orders")
    return NeedReals(Values[0]), NeedReals(Values[1]), NeedReals(Values[2])


def NeedCurve(Value: KGrammarValue) -> BsCurve:
    if not isinstance(Value, BsCurve):
        raise ValueError("Fusion typed subtype field requires a B-spline curve")
    return Value


def NeedOption(Value: KGrammarValue) -> BsCurve | None:
    return None if Value is None else NeedCurve(Value)


def NeedSheet(Value: KGrammarValue) -> BsSurface:
    if not isinstance(Value, BsSurface):
        raise ValueError("Fusion typed subtype field requires a B-spline surface")
    return Value


def NeedSubdata(Value: KGrammarValue) -> LoftSubdata:
    if not isinstance(Value, LoftSubdata):
        raise ValueError("Fusion typed subtype field requires loft subdata")
    return Value


def NeedChoice(Value: KGrammarValue) -> ChoiceValue:
    if not isinstance(Value, ChoiceValue):
        raise ValueError("Fusion typed subtype field requires a named record")
    return Value


def NeedKeyed(Value: KGrammarValue, ChoiceKey: int | str) -> KGrammarValue:
    Choice = NeedChoice(Value)
    if Choice.ChoiceKey != ChoiceKey:
        raise ValueError("Unsupported Fusion typed subtype variant")
    return Choice.Body
