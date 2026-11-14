from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SurfaceRecords import (
    CommonFrom,
    CommonTree,
    SplineCommon,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepPaths import (
    KSweepPath,
    PathFrom,
    PathTree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TreeParts import (
    IsFlagSet,
    KRange,
    KTriple,
    NeedChoice,
    NeedItems,
    NeedRange,
    NeedRecord,
    NeedTriple,
    NeedWhole,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase


@MakeDataClass(frozen=True, slots=True)
class SweepProfile(TypedBase):
    Curve: ChoiceValue
    ParamRange: KRange
    PlanarFrame: tuple[KTriple, KTriple] | None
    Position: KTriple
    FrameMatrix: tuple[KTriple, KTriple, KTriple]


@MakeDataClass(frozen=True, slots=True)
class SweepSur(TypedBase):
    Revision: int
    IsOnXy: bool
    ProfileId: int
    Profile: SweepProfile
    Path: KSweepPath
    Common: SplineCommon


def PlanarFrom(Value: KGrammarValue) -> tuple[KTriple, KTriple] | None:
    if Value is None:
        return None
    Origin, Normal = NeedItems(Value, 2)
    return NeedTriple(Origin), NeedTriple(Normal)


def SweepFrom(Value: KGrammarValue) -> SweepSur:
    Parts = NeedItems(Value, 12)
    Matrix = (NeedTriple(Parts[7]), NeedTriple(Parts[8]), NeedTriple(Parts[9]))
    Profile = SweepProfile(
        NeedChoice(Parts[3]),
        NeedRange(Parts[4]),
        PlanarFrom(Parts[5]),
        NeedTriple(Parts[6]),
        Matrix,
    )
    return SweepSur(
        NeedWhole(Parts[0]),
        IsFlagSet(Parts[1]),
        NeedWhole(Parts[2]),
        Profile,
        PathFrom(Parts[10]),
        CommonFrom(Parts[11]),
    )


def SweepTree(Value: KGrammarValue) -> KGrammarValue:
    Record = NeedRecord(Value, SweepSur)
    Profile = NeedRecord(Record.Profile, SweepProfile)
    return (
        Record.Revision,
        Record.IsOnXy,
        Record.ProfileId,
        Profile.Curve,
        Profile.ParamRange,
        Profile.PlanarFrame,
        Profile.Position,
        *Profile.FrameMatrix,
        PathTree(Record.Path),
        CommonTree(Record.Common),
    )
