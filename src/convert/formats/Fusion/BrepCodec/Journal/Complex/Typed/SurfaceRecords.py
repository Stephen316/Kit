from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TreeParts import (
    KBreaks,
    KRange,
    NeedBreaks,
    NeedItems,
    NeedKeyed,
    NeedRange,
    NeedReal,
    NeedRecord,
    NeedSheet,
    NeedWhole,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase


@MakeDataClass(frozen=True, slots=True)
class SplineCommon(TypedBase):
    ApproxSurface: BsSurface
    FitTolerance: float
    FirstBreaks: KBreaks
    SecondBreaks: KBreaks


@MakeDataClass(frozen=True, slots=True)
class ExactSplSur(TypedBase):
    Revision: int
    Common: SplineCommon
    FirstRange: KRange
    SecondRange: KRange
    RangeForm: int


def CommonFrom(Value: KGrammarValue) -> SplineCommon:
    Parts = NeedItems(NeedKeyed(Value, 0), 9)
    if Parts[8] is not None:
        raise ValueError("Fusion spline common data carries an illegal region")
    return SplineCommon(
        NeedSheet(Parts[0]),
        NeedReal(Parts[1]),
        NeedBreaks(Parts[2:5]),
        NeedBreaks(Parts[5:8]),
    )


def CommonTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, SplineCommon)
    Parts = (
        Record.ApproxSurface,
        Record.FitTolerance,
        *Record.FirstBreaks,
        *Record.SecondBreaks,
        None,
    )
    return ChoiceValue(0, Parts)


def ExactSheetFrom(Value: KGrammarValue) -> ExactSplSur:
    Revision, Common, FirstRange, SecondRange, RangeForm = NeedItems(Value, 5)
    return ExactSplSur(
        NeedWhole(Revision),
        CommonFrom(Common),
        NeedRange(FirstRange),
        NeedRange(SecondRange),
        NeedWhole(RangeForm),
    )


def ExactSheetTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, ExactSplSur)
    return (
        Record.Revision,
        CommonTree(Record.Common),
        Record.FirstRange,
        Record.SecondRange,
        Record.RangeForm,
    )
