from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SurfaceRecords import (
    CommonFrom,
    CommonTree,
    SplineCommon,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TreeParts import (
    IsFlagSet,
    KRange,
    KTriple,
    NeedChoice,
    NeedItems,
    NeedOption,
    NeedRange,
    NeedReal,
    NeedRecord,
    NeedText,
    NeedTriple,
    NeedWhole,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase

KOffsetKinds = ("edge_offset", "fixed_width")


@MakeDataClass(frozen=True, slots=True)
class BlendSupport(TypedBase):
    SupportKind: str
    Surface: ChoiceValue
    Curve: ChoiceValue
    FirstPcurve: BsCurve | None
    Position: KTriple
    SecondPcurve: BsCurve | None
    SampleCount: int
    ThirdPcurve: BsCurve | None


@MakeDataClass(frozen=True, slots=True)
class OffsetRadius(TypedBase):
    RadiusKind: str
    LeadEnum: int
    IsCalibrated: bool
    FirstParam: float
    SecondParam: float
    OffsetValue: float


@MakeDataClass(frozen=True, slots=True)
class InterpSample(TypedBase):
    Values: tuple[float, float, float, float]
    Position: KTriple
    Direction: KTriple


@MakeDataClass(frozen=True, slots=True)
class InterpRadius(TypedBase):
    LeadEnum: int
    IsCalibrated: bool
    FirstParam: float
    SecondParam: float
    Spline: BsCurve | None
    SampleForm: int
    Samples: tuple[InterpSample, ...]


@MakeDataClass(frozen=True, slots=True)
class BlendFrame(TypedBase):
    FirstRange: KRange
    SecondRange: KRange
    FirstByte: int
    ReqTolerance: float
    FitTolerance: float
    SecondByte: int
    Common: SplineCommon
    HapCaches: tuple[int, int, int]


KRadius: TypeAlias = OffsetRadius | InterpRadius


def SupportFrom(Value: KGrammarValue) -> BlendSupport:
    Parts = NeedItems(Value, 8)
    return BlendSupport(
        NeedText(Parts[0]),
        NeedChoice(Parts[1]),
        NeedChoice(Parts[2]),
        NeedOption(Parts[3]),
        NeedTriple(Parts[4]),
        NeedOption(Parts[5]),
        NeedWhole(Parts[6]),
        NeedOption(Parts[7]),
    )


def SupportTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, BlendSupport)
    return (
        Record.SupportKind,
        Record.Surface,
        Record.Curve,
        Record.FirstPcurve,
        Record.Position,
        Record.SecondPcurve,
        Record.SampleCount,
        Record.ThirdPcurve,
    )


def SampleFrom(Value: KGrammarValue) -> InterpSample:
    Parts = NeedItems(Value, 6)
    Values = (
        NeedReal(Parts[0]),
        NeedReal(Parts[1]),
        NeedReal(Parts[2]),
        NeedReal(Parts[3]),
    )
    return InterpSample(Values, NeedTriple(Parts[4]), NeedTriple(Parts[5]))


def RadiusFrom(Value: KGrammarValue) -> KRadius:
    Choice = NeedChoice(Value)
    if Choice.ChoiceKey in KOffsetKinds:
        Parts = NeedItems(Choice.Body, 5)
        return OffsetRadius(
            NeedText(Choice.ChoiceKey),
            NeedWhole(Parts[0]),
            IsFlagSet(Parts[1]),
            NeedReal(Parts[2]),
            NeedReal(Parts[3]),
            NeedReal(Parts[4]),
        )
    if Choice.ChoiceKey != "interp":
        raise ValueError("Unsupported Fusion blend radius variant")
    Parts = NeedItems(Choice.Body, 7)
    return InterpRadius(
        NeedWhole(Parts[0]),
        IsFlagSet(Parts[1]),
        NeedReal(Parts[2]),
        NeedReal(Parts[3]),
        NeedOption(Parts[4]),
        NeedWhole(Parts[5]),
        tuple(SampleFrom(Element) for Element in NeedItems(Parts[6], None)),
    )


def RadiusTree(Value: KGrammarValue) -> KGrammarValue:
    if isinstance(Value, OffsetRadius):
        if Value.RadiusKind not in KOffsetKinds:
            raise ValueError("Unsupported Fusion blend radius variant")
        HeadParts = (Value.LeadEnum, Value.IsCalibrated, Value.FirstParam)
        return ChoiceValue(
            Value.RadiusKind, (*HeadParts, Value.SecondParam, Value.OffsetValue)
        )
    Record = NeedRecord(Value, InterpRadius)
    Samples = tuple(
        (*Sample.Values, Sample.Position, Sample.Direction)
        for Sample in (NeedRecord(Element, InterpSample) for Element in Record.Samples)
    )
    Parts = (
        Record.LeadEnum,
        Record.IsCalibrated,
        Record.FirstParam,
        Record.SecondParam,
        Record.Spline,
        Record.SampleForm,
        Samples,
    )
    return ChoiceValue("interp", Parts)


def FrameFrom(Parts: tuple[KGrammarValue, ...]) -> BlendFrame:
    if len(Parts) != 10:
        raise ValueError("Fusion blend frame disagrees with its grammar")
    return BlendFrame(
        NeedRange(Parts[0]),
        NeedRange(Parts[1]),
        NeedWhole(Parts[2]),
        NeedReal(Parts[3]),
        NeedReal(Parts[4]),
        NeedWhole(Parts[5]),
        CommonFrom(Parts[6]),
        (NeedWhole(Parts[7]), NeedWhole(Parts[8]), NeedWhole(Parts[9])),
    )


def FrameTree(Value: KGrammarValue) -> tuple[KGrammarValue, ...]:
    Record = NeedRecord(Value, BlendFrame)
    return (
        Record.FirstRange,
        Record.SecondRange,
        Record.FirstByte,
        Record.ReqTolerance,
        Record.FitTolerance,
        Record.SecondByte,
        CommonTree(Record.Common),
        *Record.HapCaches,
    )
