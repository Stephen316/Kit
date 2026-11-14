from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
    LoftSubdata,
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
    NeedCurve,
    NeedItems,
    NeedOption,
    NeedRange,
    NeedReal,
    NeedRecord,
    NeedSubdata,
    NeedTriple,
    NeedWhole,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase


@MakeDataClass(frozen=True, slots=True)
class LoftPiece(TypedBase):
    PieceKind: int
    Curve: ChoiceValue
    Surface: ChoiceValue | None
    FirstPcurve: BsCurve | None
    SecondPcurve: BsCurve | None
    PieceFlag: bool | None
    ReparamInt: int
    Reparam: LoftSubdata
    PieceVector: KTriple | None


@MakeDataClass(frozen=True, slots=True)
class LoftSection(TypedBase):
    SectionValue: float
    Pieces: tuple[LoftPiece, ...]
    SectionCurve: ChoiceValue
    Wrappers: tuple[BsCurve, ...]
    TrailInt: int


@MakeDataClass(frozen=True, slots=True)
class LoftSplSur(TypedBase):
    Revision: int
    FirstSections: tuple[LoftSection, ...]
    SecondSections: tuple[LoftSection, ...]
    FirstRange: KRange
    SecondRange: KRange
    LoftFlags: tuple[bool, bool, bool, bool]
    TrailInts: tuple[int, int]
    Common: SplineCommon


def PieceFrom(Value: KGrammarValue) -> LoftPiece:
    Choice = NeedChoice(Value)
    PieceKind = NeedWhole(Choice.ChoiceKey)
    Parts = NeedItems(Choice.Body, 4 if PieceKind == 0 else 5)
    Reparam, Subdata, Vector = NeedItems(Parts[-1], 3)
    Surface = None if PieceKind == 0 else NeedChoice(Parts[1])
    Second = NeedOption(Parts[2]) if PieceKind == 0 else None
    return LoftPiece(
        PieceKind,
        NeedChoice(Parts[0]),
        Surface,
        NeedOption(Parts[1 if PieceKind == 0 else 2]),
        Second,
        None if PieceKind == 0 else IsFlagSet(Parts[3]),
        NeedWhole(Reparam),
        NeedSubdata(Subdata),
        None if Vector is None else NeedTriple(Vector),
    )


def PieceTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, LoftPiece)
    Trail = (Record.ReparamInt, Record.Reparam, Record.PieceVector)
    Shared = (Record.Curve,)
    if Record.PieceKind == 0:
        if Record.Surface is not None or Record.PieceFlag is not None:
            raise ValueError("Fusion loft piece fields disagree with its kind")
        Parts = (*Shared, Record.FirstPcurve, Record.SecondPcurve, Trail)
        return ChoiceValue(0, Parts)
    if Record.SecondPcurve is not None:
        raise ValueError("Fusion loft piece fields disagree with its kind")
    Middle = (Record.Surface, Record.FirstPcurve, Record.PieceFlag)
    return ChoiceValue(Record.PieceKind, (*Shared, *Middle, Trail))


def SectionFrom(Value: KGrammarValue) -> LoftSection:
    SectionValue, Pieces, PathParts = NeedItems(Value, 3)
    Curve, Wrappers, TrailInt = NeedItems(PathParts, 3)
    return LoftSection(
        NeedReal(SectionValue),
        tuple(PieceFrom(Element) for Element in NeedItems(Pieces, None)),
        NeedChoice(Curve),
        tuple(NeedCurve(Element) for Element in NeedItems(Wrappers, None)),
        NeedWhole(TrailInt),
    )


def SectionTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, LoftSection)
    Pieces = tuple(PieceTree(Element) for Element in Record.Pieces)
    PathParts = (Record.SectionCurve, Record.Wrappers, Record.TrailInt)
    return Record.SectionValue, Pieces, PathParts


def LoftFrom(Value: KGrammarValue) -> LoftSplSur:
    Parts = NeedItems(Value, 12)
    Flags = (
        IsFlagSet(Parts[5]),
        IsFlagSet(Parts[6]),
        IsFlagSet(Parts[7]),
        IsFlagSet(Parts[8]),
    )
    return LoftSplSur(
        NeedWhole(Parts[0]),
        tuple(SectionFrom(Element) for Element in NeedItems(Parts[1], None)),
        tuple(SectionFrom(Element) for Element in NeedItems(Parts[2], None)),
        NeedRange(Parts[3]),
        NeedRange(Parts[4]),
        Flags,
        (NeedWhole(Parts[9]), NeedWhole(Parts[10])),
        CommonFrom(Parts[11]),
    )


def LoftTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, LoftSplSur)
    return (
        Record.Revision,
        tuple(SectionTree(Element) for Element in Record.FirstSections),
        tuple(SectionTree(Element) for Element in Record.SecondSections),
        Record.FirstRange,
        Record.SecondRange,
        *Record.LoftFlags,
        *Record.TrailInts,
        CommonTree(Record.Common),
    )
