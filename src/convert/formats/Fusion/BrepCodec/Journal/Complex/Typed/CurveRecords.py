from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TreeParts import (
    IsFlagSet,
    KBreaks,
    KRange,
    NeedBreaks,
    NeedChoice,
    NeedCurve,
    NeedItems,
    NeedKeyed,
    NeedOption,
    NeedRange,
    NeedReal,
    NeedRecord,
    NeedWhole,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase


@MakeDataClass(frozen=True, slots=True)
class CurveContext(TypedBase):
    Revision: int
    ApproxCurve: BsCurve
    FitTolerance: float
    FirstSurface: ChoiceValue
    SecondSurface: ChoiceValue
    FirstPcurve: BsCurve | None
    SecondPcurve: BsCurve | None
    ParamRange: KRange
    Discontinuities: KBreaks
    HapCache: int


@MakeDataClass(frozen=True, slots=True)
class ExpParCur(TypedBase):
    Spline: BsCurve
    FitTolerance: float
    Surface: ChoiceValue


@MakeDataClass(frozen=True, slots=True)
class ExactIntCur(TypedBase):
    Context: CurveContext
    RangeBounds: KRange
    LowEndForm: int
    HighEndForm: int


@MakeDataClass(frozen=True, slots=True)
class ParIntCur(TypedBase):
    Context: CurveContext
    IsSurfOne: bool
    ExtraFlag: bool


@MakeDataClass(frozen=True, slots=True)
class IntIntCur(TypedBase):
    Context: CurveContext


@MakeDataClass(frozen=True, slots=True)
class SpringIntCur(TypedBase):
    Context: CurveContext
    SpringSide: int


def ContextFrom(Value: KGrammarValue) -> CurveContext:
    Revision, Approximation = NeedItems(Value, 2)
    Parts = NeedItems(NeedKeyed(Approximation, 0), 11)
    return CurveContext(
        NeedWhole(Revision),
        NeedCurve(Parts[0]),
        NeedReal(Parts[1]),
        NeedChoice(Parts[2]),
        NeedChoice(Parts[3]),
        NeedOption(Parts[4]),
        NeedOption(Parts[5]),
        NeedRange(Parts[6]),
        NeedBreaks(Parts[7:10]),
        NeedWhole(Parts[10]),
    )


def ContextTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, CurveContext)
    Parts = (
        Record.ApproxCurve,
        Record.FitTolerance,
        Record.FirstSurface,
        Record.SecondSurface,
        Record.FirstPcurve,
        Record.SecondPcurve,
        Record.ParamRange,
        *Record.Discontinuities,
        Record.HapCache,
    )
    return Record.Revision, ChoiceValue(0, Parts)


def PcurveFrom(Value: KGrammarValue) -> ExpParCur:
    Spline, Tolerance, Surface = NeedItems(Value, 3)
    return ExpParCur(NeedCurve(Spline), NeedReal(Tolerance), NeedChoice(Surface))


def PcurveTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, ExpParCur)
    return Record.Spline, Record.FitTolerance, Record.Surface


def ExactCurveFrom(Value: KGrammarValue) -> ExactIntCur:
    Context, Bounds, LowEnd, HighEnd = NeedItems(Value, 4)
    return ExactIntCur(
        ContextFrom(Context), NeedRange(Bounds), NeedWhole(LowEnd), NeedWhole(HighEnd)
    )


def ExactCurveTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, ExactIntCur)
    Context = ContextTree(Record.Context)
    return Context, Record.RangeBounds, Record.LowEndForm, Record.HighEndForm


def ParCurveFrom(Value: KGrammarValue) -> ParIntCur:
    Context, SurfOne, Extra = NeedItems(Value, 3)
    return ParIntCur(ContextFrom(Context), IsFlagSet(SurfOne), IsFlagSet(Extra))


def ParCurveTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, ParIntCur)
    return ContextTree(Record.Context), Record.IsSurfOne, Record.ExtraFlag


def IntCurveFrom(Value: KGrammarValue) -> IntIntCur:
    (Context,) = NeedItems(Value, 1)
    return IntIntCur(ContextFrom(Context))


def IntCurveTree(Value: KGrammarValue) -> KGrammarValue:
    return (ContextTree(NeedRecord(Value, IntIntCur).Context),)


def SpringFrom(Value: KGrammarValue) -> SpringIntCur:
    Context, SideValue = NeedItems(Value, 2)
    return SpringIntCur(ContextFrom(Context), NeedWhole(SideValue))


def SpringTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, SpringIntCur)
    return ContextTree(Record.Context), Record.SpringSide
