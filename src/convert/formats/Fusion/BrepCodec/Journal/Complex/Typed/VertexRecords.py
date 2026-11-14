from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TreeParts import (
    IsFlagSet,
    KTriple,
    NeedChoice,
    NeedItems,
    NeedKeyed,
    NeedOption,
    NeedReal,
    NeedRecord,
    NeedTriple,
    NeedWhole,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase


@MakeDataClass(frozen=True, slots=True)
class VblBoundary(TypedBase):
    IsCross: bool
    MagicVector: KTriple
    FirstSmooth: bool
    SecondSmooth: bool
    BoundaryValue: float
    Surface: ChoiceValue
    Spline: BsCurve | None
    IsReversed: bool
    FitTolerance: float


@MakeDataClass(frozen=True, slots=True)
class VblSurf(TypedBase):
    Revision: int
    Boundaries: tuple[VblBoundary, ...]
    TrailInt: int
    FitTolerance: float


def BoundaryFrom(Value: KGrammarValue) -> VblBoundary:
    Parts = NeedItems(NeedKeyed(Value, "pcurve"), 9)
    return VblBoundary(
        IsFlagSet(Parts[0]),
        NeedTriple(Parts[1]),
        IsFlagSet(Parts[2]),
        IsFlagSet(Parts[3]),
        NeedReal(Parts[4]),
        NeedChoice(Parts[5]),
        NeedOption(Parts[6]),
        IsFlagSet(Parts[7]),
        NeedReal(Parts[8]),
    )


def BoundaryTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, VblBoundary)
    Parts = (
        Record.IsCross,
        Record.MagicVector,
        Record.FirstSmooth,
        Record.SecondSmooth,
        Record.BoundaryValue,
        Record.Surface,
        Record.Spline,
        Record.IsReversed,
        Record.FitTolerance,
    )
    return ChoiceValue("pcurve", Parts)


def VertexFrom(Value: KGrammarValue) -> VblSurf:
    Revision, Boundaries, TrailInt, Tolerance = NeedItems(Value, 4)
    return VblSurf(
        NeedWhole(Revision),
        tuple(BoundaryFrom(Element) for Element in NeedItems(Boundaries, None)),
        NeedWhole(TrailInt),
        NeedReal(Tolerance),
    )


def VertexTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, VblSurf)
    Boundaries = tuple(BoundaryTree(Element) for Element in Record.Boundaries)
    return Record.Revision, Boundaries, Record.TrailInt, Record.FitTolerance
