from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.TreeParts import (
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
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase


# curve context needs an explicit state contract so native geometry variants retain distinct field contracts
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


# exp par cur needs an explicit state contract so native geometry variants retain distinct field contracts
@MakeDataClass(frozen=True, slots=True)
class ExpParCur(TypedBase):
    Spline: BsCurve
    FitTolerance: float
    Surface: ChoiceValue


# exact int cur needs an explicit state contract so native geometry variants retain distinct field contracts
@MakeDataClass(frozen=True, slots=True)
class ExactIntCur(TypedBase):
    Context: CurveContext
    RangeBounds: KRange
    LowEndForm: int
    HighEndForm: int


# par int cur needs an explicit state contract so native geometry variants retain distinct field contracts
@MakeDataClass(frozen=True, slots=True)
class ParIntCur(TypedBase):
    Context: CurveContext
    IsSurfOne: bool
    ExtraFlag: bool


# int int cur needs an explicit state contract so native geometry variants retain distinct field contracts
@MakeDataClass(frozen=True, slots=True)
class IntIntCur(TypedBase):
    Context: CurveContext


# spring int cur needs an explicit state contract so native geometry variants retain distinct field contracts
@MakeDataClass(frozen=True, slots=True)
class SpringIntCur(TypedBase):
    Context: CurveContext
    SpringSide: int


# the context from contract needs a shared interpretation so native geometry variants retain distinct field contracts
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


# the context tree contract needs a shared interpretation so native geometry variants retain distinct field contracts
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


# the pcurve from contract needs a shared interpretation so native geometry variants retain distinct field contracts
def PcurveFrom(Value: KGrammarValue) -> ExpParCur:
    Spline, Tolerance, Surface = NeedItems(Value, 3)
    return ExpParCur(NeedCurve(Spline), NeedReal(Tolerance), NeedChoice(Surface))


# the pcurve tree contract needs a shared interpretation so native geometry variants retain distinct field contracts
def PcurveTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, ExpParCur)
    return Record.Spline, Record.FitTolerance, Record.Surface


# the exact curve from contract needs a shared interpretation so native geometry variants retain distinct field contracts
def ExactCurveFrom(Value: KGrammarValue) -> ExactIntCur:
    Context, Bounds, LowEnd, HighEnd = NeedItems(Value, 4)
    return ExactIntCur(
        ContextFrom(Context), NeedRange(Bounds), NeedWhole(LowEnd), NeedWhole(HighEnd)
    )


# the exact curve tree contract needs a shared interpretation so native geometry variants retain distinct field contracts
def ExactCurveTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, ExactIntCur)
    Context = ContextTree(Record.Context)
    return Context, Record.RangeBounds, Record.LowEndForm, Record.HighEndForm


# the par curve from contract needs a shared interpretation so native geometry variants retain distinct field contracts
def ParCurveFrom(Value: KGrammarValue) -> ParIntCur:
    Context, SurfOne, Extra = NeedItems(Value, 3)
    return ParIntCur(ContextFrom(Context), IsFlagSet(SurfOne), IsFlagSet(Extra))


# the par curve tree contract needs a shared interpretation so native geometry variants retain distinct field contracts
def ParCurveTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, ParIntCur)
    return ContextTree(Record.Context), Record.IsSurfOne, Record.ExtraFlag


# the int curve from contract needs a shared interpretation so native geometry variants retain distinct field contracts
def IntCurveFrom(Value: KGrammarValue) -> IntIntCur:
    (Context,) = NeedItems(Value, 1)
    return IntIntCur(ContextFrom(Context))


# the int curve tree contract needs a shared interpretation so native geometry variants retain distinct field contracts
def IntCurveTree(Value: KGrammarValue) -> KGrammarValue:
    return (ContextTree(NeedRecord(Value, IntIntCur).Context),)


# the spring from contract needs a shared interpretation so native geometry variants retain distinct field contracts
def SpringFrom(Value: KGrammarValue) -> SpringIntCur:
    Context, SideValue = NeedItems(Value, 2)
    return SpringIntCur(ContextFrom(Context), NeedWhole(SideValue))


# the spring tree contract needs a shared interpretation so native geometry variants retain distinct field contracts
def SpringTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, SpringIntCur)
    return ContextTree(Record.Context), Record.SpringSide
