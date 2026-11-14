from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.BlendParts import (
    BlendFrame,
    BlendSupport,
    FrameFrom,
    FrameTree,
    KRadius,
    RadiusFrom,
    RadiusTree,
    SupportFrom,
    SupportTree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TreeParts import (
    IsFlagSet,
    KRange,
    NeedChoice,
    NeedItems,
    NeedOption,
    NeedRange,
    NeedReal,
    NeedRecord,
    NeedWhole,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase


@MakeDataClass(frozen=True, slots=True)
class SrfSrfBlend(TypedBase):
    Revision: int
    FirstSupport: BlendSupport
    SecondSupport: BlendSupport
    BlendCurve: ChoiceValue
    FirstValue: float
    SecondValue: float
    RadiusForm: int
    FirstRadius: KRadius
    SecondRadius: KRadius | None
    Frame: BlendFrame
    VarBlendCurve: ChoiceValue
    IsConvex: bool
    IsEnvelope: bool
    VarBlendRange: KRange
    VarBlendSpline: BsCurve | None


@MakeDataClass(frozen=True, slots=True)
class GtwoBlend(TypedBase):
    Revision: int
    FirstGtwoReal: float
    SecondGtwoReal: float
    FirstSupport: BlendSupport
    SecondSupport: BlendSupport
    BlendCurve: ChoiceValue
    FirstValue: float
    SecondValue: float
    Frame: BlendFrame


def RadiiFrom(Value: KGrammarValue) -> tuple[int, KRadius, KRadius | None]:
    Choice = NeedChoice(Value)
    FormValue = NeedWhole(Choice.ChoiceKey)
    if FormValue != 1:
        return FormValue, RadiusFrom(Choice.Body), None
    First, Second = NeedItems(Choice.Body, 2)
    return FormValue, RadiusFrom(First), RadiusFrom(Second)


def RadiiTree(Record: SrfSrfBlend) -> ChoiceValue:
    if (Record.RadiusForm == 1) != (Record.SecondRadius is not None):
        raise ValueError("Fusion blend radius form disagrees with its radii")
    First = RadiusTree(Record.FirstRadius)
    if Record.SecondRadius is None:
        return ChoiceValue(Record.RadiusForm, First)
    return ChoiceValue(Record.RadiusForm, (First, RadiusTree(Record.SecondRadius)))


def RollFrom(Value: KGrammarValue) -> SrfSrfBlend:
    Parts = NeedItems(Value, 24)
    if Parts[7] is not None or Parts[23] is not None:
        raise ValueError("Fusion blend fixed field carries a value")
    FormValue, FirstRadius, SecondRadius = RadiiFrom(Parts[6])
    return SrfSrfBlend(
        NeedWhole(Parts[0]),
        SupportFrom(Parts[1]),
        SupportFrom(Parts[2]),
        NeedChoice(Parts[3]),
        NeedReal(Parts[4]),
        NeedReal(Parts[5]),
        FormValue,
        FirstRadius,
        SecondRadius,
        FrameFrom(Parts[8:18]),
        NeedChoice(Parts[18]),
        IsFlagSet(Parts[19]),
        IsFlagSet(Parts[20]),
        NeedRange(Parts[21]),
        NeedOption(Parts[22]),
    )


def RollTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, SrfSrfBlend)
    return (
        Record.Revision,
        SupportTree(Record.FirstSupport),
        SupportTree(Record.SecondSupport),
        Record.BlendCurve,
        Record.FirstValue,
        Record.SecondValue,
        RadiiTree(Record),
        None,
        *FrameTree(Record.Frame),
        Record.VarBlendCurve,
        Record.IsConvex,
        Record.IsEnvelope,
        Record.VarBlendRange,
        Record.VarBlendSpline,
        None,
    )


def GtwoFrom(Value: KGrammarValue) -> GtwoBlend:
    Parts = NeedItems(Value, 19)
    if Parts[8] is not None:
        raise ValueError("Fusion blend fixed field carries a value")
    return GtwoBlend(
        NeedWhole(Parts[0]),
        NeedReal(Parts[1]),
        NeedReal(Parts[2]),
        SupportFrom(Parts[3]),
        SupportFrom(Parts[4]),
        NeedChoice(Parts[5]),
        NeedReal(Parts[6]),
        NeedReal(Parts[7]),
        FrameFrom(Parts[9:19]),
    )


def GtwoTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, GtwoBlend)
    return (
        Record.Revision,
        Record.FirstGtwoReal,
        Record.SecondGtwoReal,
        SupportTree(Record.FirstSupport),
        SupportTree(Record.SecondSupport),
        Record.BlendCurve,
        Record.FirstValue,
        Record.SecondValue,
        None,
        *FrameTree(Record.Frame),
    )
