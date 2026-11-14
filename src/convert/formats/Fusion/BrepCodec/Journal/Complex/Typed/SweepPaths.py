from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TreeParts import (
    IsFlagSet,
    KRange,
    KTriple,
    NeedChoice,
    NeedItems,
    NeedRange,
    NeedReal,
    NeedReals,
    NeedRecord,
    NeedTriple,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase


@MakeDataClass(frozen=True, slots=True)
class PathHead(TypedBase):
    IsNoZ: bool
    PathCurve: ChoiceValue
    PathRange: KRange
    PathReal: float
    HasScale: bool


@MakeDataClass(frozen=True, slots=True)
class LawPath(TypedBase):
    Header: PathHead
    Formula: ChoiceValue
    IsTwistPeriodic: bool


@MakeDataClass(frozen=True, slots=True)
class RailPath(TypedBase):
    Header: PathHead
    IsNoRail: bool
    RailCurve: ChoiceValue
    RailRange: KRange
    CrossValues: tuple[tuple[float, ...], tuple[float, ...]]
    TrailFlags: tuple[bool, bool, bool]


@MakeDataClass(frozen=True, slots=True)
class NormalPath(TypedBase):
    Header: PathHead
    Surface: ChoiceValue
    TrailFlag: bool


@MakeDataClass(frozen=True, slots=True)
class TwistPath(TypedBase):
    Header: PathHead
    InnerPath: "KSweepPath"
    Position: KTriple
    PathVector: KTriple
    FirstReal: float
    SecondReal: float


KSweepPath: TypeAlias = LawPath | RailPath | NormalPath | TwistPath


def HeadFrom(Railhead: KGrammarValue, Scale: KGrammarValue) -> PathHead:
    NoZFlag, Curve, Bounds, RealValue = NeedItems(Railhead, 4)
    return PathHead(
        IsFlagSet(NoZFlag),
        NeedChoice(Curve),
        NeedRange(Bounds),
        NeedReal(RealValue),
        IsFlagSet(Scale),
    )


def HeadTree(Value: KGrammarValue) -> tuple[KGrammarValue, KGrammarValue]:
    Header = NeedRecord(Value, PathHead)
    Railhead = (Header.IsNoZ, Header.PathCurve, Header.PathRange, Header.PathReal)
    return Railhead, Header.HasScale


def RailFrom(Header: PathHead, Parts: tuple[KGrammarValue, ...]) -> RailPath:
    if len(Parts) != 7:
        raise ValueError("Fusion sweep rail path disagrees with its grammar")
    Leaders, Trailers = NeedItems(Parts[3], 2)
    return RailPath(
        Header,
        IsFlagSet(Parts[0]),
        NeedChoice(Parts[1]),
        NeedRange(Parts[2]),
        (NeedReals(Leaders), NeedReals(Trailers)),
        (IsFlagSet(Parts[4]), IsFlagSet(Parts[5]), IsFlagSet(Parts[6])),
    )


def TwistFrom(Header: PathHead, Parts: tuple[KGrammarValue, ...]) -> TwistPath:
    if len(Parts) != 5:
        raise ValueError("Fusion sweep twist path disagrees with its grammar")
    return TwistPath(
        Header,
        PathFrom(Parts[0]),
        NeedTriple(Parts[1]),
        NeedTriple(Parts[2]),
        NeedReal(Parts[3]),
        NeedReal(Parts[4]),
    )


def PathFrom(Value: KGrammarValue) -> KSweepPath:
    Choice = NeedChoice(Value)
    Parts = NeedItems(Choice.Body, None)
    if len(Parts) < 2:
        raise ValueError("Fusion sweep path disagrees with its grammar")
    Header, Remainder = HeadFrom(Parts[0], Parts[1]), Parts[2:]
    if Choice.ChoiceKey == 1 and len(Remainder) == 2:
        return LawPath(Header, NeedChoice(Remainder[0]), IsFlagSet(Remainder[1]))
    if Choice.ChoiceKey == 2:
        return RailFrom(Header, Remainder)
    if Choice.ChoiceKey == 3 and len(Remainder) == 3 and Remainder[1] is None:
        return NormalPath(Header, NeedChoice(Remainder[0]), IsFlagSet(Remainder[2]))
    if Choice.ChoiceKey == 5:
        return TwistFrom(Header, Remainder)
    raise ValueError("Unsupported Fusion sweep path variant")


def PathTree(Value: KGrammarValue) -> ChoiceValue:
    if isinstance(Value, LawPath):
        LawParts = (Value.Formula, Value.IsTwistPeriodic)
        return ChoiceValue(1, (*HeadTree(Value.Header), *LawParts))
    if isinstance(Value, RailPath):
        RailParts = (Value.IsNoRail, Value.RailCurve, Value.RailRange)
        CrossParts = (Value.CrossValues, *Value.TrailFlags)
        return ChoiceValue(2, (*HeadTree(Value.Header), *RailParts, *CrossParts))
    if isinstance(Value, NormalPath):
        NormalParts = (Value.Surface, None, Value.TrailFlag)
        return ChoiceValue(3, (*HeadTree(Value.Header), *NormalParts))
    Record = NeedRecord(Value, TwistPath)
    TwistParts = (PathTree(Record.InnerPath), Record.Position, Record.PathVector)
    RealParts = (Record.FirstReal, Record.SecondReal)
    return ChoiceValue(5, (*HeadTree(Record.Header), *TwistParts, *RealParts))
