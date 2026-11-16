from dataclasses import replace as ReplaceValue
from math import radians as Radians, tan as Tangent

from convert.Formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.EdgeRound import EdgeRound
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Construct.WorkCorner import (
    CornerWalls,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Hole.HoleSolid import HoleSolid
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Bodies.CheckBodies import (
    KBodyLimit,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Bodies.BodyStage import (
    BodyStageMut,
    KBodySpecs,
    KBodyState,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import (
    FamilyOf,
    IsStateless,
    OperationsOf,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Loft.LoftSolid import LoftSolid
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Sweep.SweepSolid import (
    SweepProfile,
    SweepSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Pattern.PatternSolid import (
    CopySolid,
    KCopySpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    PlanSketch,
    SketchPlan,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Revolve.RevolveSolid import (
    ApplyRevolve,
    RevolveProfile,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.BlockSolid import (
    BlockSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.EditCorner import (
    EditCorner,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ExtrudeSolid import (
    ExtrudeSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Move.MoveSolid import MoveSolid
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Draft.DraftSolid import (
    DraftSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Offset.OffsetSolid import (
    OffsetSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.HollowSolid import (
    HollowSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import IsSealed
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ToolSlab import (
    ToolEdgeTags,
    ToolLabels,
    ToolSlab,
)

# base sketch tags must remain consistent across callers so feature parameters remain connected to the resulting geometry
KBaseSketchTags = 9


# apply extrude needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def ApplyExtrude(
    Solid: PrismSolid | None, Feature: ExtrudeSpec, Operation: int, Sketched: SketchPlan
) -> PrismSolid:
    Shaper = ToolSlab(Feature, Operation + 1)
    Curves = tuple(
        (Label, Segment.CurveTag)
        for Label, Segment in zip(ToolLabels(Feature, Operation + 1), Sketched.Edges)
    )
    BodyLabel = FaceLabel(str(Operation + 1), (), len(Feature.Profile) + 3)
    Tagged = ToolEdgeTags(Feature, Operation + 1, Sketched.Edges[0].CurveTag)
    if Feature.Operation == "new":
        return PrismSolid((Shaper,), BodyLabel, Curves, Tagged)
    if Solid is None:
        raise ValueError("Fusion part extrude requires an existing body")
    Joined = BodyLabel if Feature.Operation == "join" else None
    Result = ExtrudeSolid(Solid, Shaper, Feature.Operation, Joined)
    return ReplaceValue(
        Result,
        SketchCurves=Solid.SketchCurves + Curves,
        EdgeTags=Solid.EdgeTags + Tagged,
    )


# the bevel legs contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def BevelLegs(Feature: FilletSpec | ChamferSpec) -> tuple[float, float]:
    if isinstance(Feature, FilletSpec):
        return Feature.RadiusMm / 10.0, Feature.RadiusMm / 10.0
    Amount = Feature.DistanceMm / 10.0
    if Feature.SecondMm > 0:
        return Amount, Feature.SecondMm / 10.0
    if Feature.AngleDegrees > 0:
        return Amount, Amount * Tangent(Radians(Feature.AngleDegrees))
    return Amount, Amount


# the round solid contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def RoundSolid(
    Solid: PrismSolid, Feature: FilletSpec | ChamferSpec, Operation: int
) -> PrismSolid:
    Level = (Feature.LevelMm or 0.0) / 10.0
    Points = tuple(
        (PointMm[0] / 10.0, PointMm[1] / 10.0, Level)
        for PointMm in (Feature.CornerMm, *Feature.MoreCornersMm)
    )
    FirstCm, SecondCm = BevelLegs(Feature)
    Rounded = isinstance(Feature, FilletSpec)
    Round = EdgeRound(Points, FirstCm, SecondCm, Rounded, Operation, Solid.Blends)
    Result = ReplaceValue(Solid, Rounds=(*Solid.Rounds, Round))
    _ = BuildShape(Result)
    return Result


# the corner solid contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def CornerSolid(
    Solid: PrismSolid, Feature: FilletSpec | ChamferSpec, Operation: int
) -> PrismSolid:
    if Feature.LevelMm is not None:
        return RoundSolid(Solid, Feature, Operation)
    Rounded = isinstance(Feature, FilletSpec)
    if isinstance(Feature, FilletSpec):
        Amount, Bevel = Feature.RadiusMm / 10.0, (0.0, 0.0)
    else:
        Amount = Feature.DistanceMm / 10.0
        Bevel = (Feature.SecondMm / 10.0, Radians(Feature.AngleDegrees))
    for Index, CornerMm in enumerate((Feature.CornerMm, *Feature.MoreCornersMm)):
        Corner = (CornerMm[0] / 10.0, CornerMm[1] / 10.0)
        Label = FaceLabel(str(Index + 1), (Operation,))
        Solid = EditCorner(Solid, Corner, Amount, Label, Rounded, Bevel)
        if Rounded:
            Solid = ReplaceValue(Solid, Blends=(*Solid.Blends, Label))
    return Solid


# apply feature needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def ApplyFeature(
    Solid: PrismSolid | None, Feature: KPartFeature, Operation: int
) -> PrismSolid:
    if Solid is None:
        raise ValueError("Fusion part features require a body from a new extrude")
    if isinstance(Feature, (FilletSpec, ChamferSpec)):
        return CornerSolid(Solid, Feature, Operation)
    if isinstance(Feature, (ExtrudeSpec, RevolveSpec)):
        raise ValueError("Fusion part extrudes require a sketch plan")
    if isinstance(Feature, HoleSpec):
        return HoleSolid(Solid, Feature, Operation)
    if isinstance(Feature, MoveSpec):
        return MoveSolid(Solid, Feature)
    if isinstance(Feature, OffsetSpec):
        return OffsetSolid(Solid, Feature, Operation)
    if isinstance(Feature, DraftSpec):
        return DraftSolid(Solid, Feature, Operation)
    if isinstance(Feature, PlaneSpec):
        return Solid
    if isinstance(Feature, (AxisSpec, PointSpec)):
        _ = CornerWalls(Solid, (Feature.CornerMm[0] / 10.0, Feature.CornerMm[1] / 10.0))
        return Solid
    if isinstance(Feature, (PatternSpec, CircularSpec, MirrorSpec)):
        raise ValueError("Fusion part copies require their source stage")
    if not isinstance(Feature, ShellSpec):
        raise ValueError("Fusion body features change bodies as a whole")
    Sides = tuple((Point[0] / 10.0, Point[1] / 10.0) for Point in Feature.SidesMm)
    return HollowSolid(Solid, Feature.ThicknessMm / 10.0, Operation, Sides)


# the base solid contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def BaseSolid(SpecValue: DocumentSpec, Policy: AuthorPolicy) -> PrismSolid | None:
    if SpecValue.ProfileKind == "part":
        return None
    return BlockSolid(
        SpecValue.WidthMm / 10.0,
        SpecValue.DepthMm / 10.0,
        SpecValue.LengthMm / 10.0,
        Policy,
    )


# copy context needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def CopyContext(
    Features: tuple[KPartFeature, ...], Feature: KCopySpec, Index: int
) -> tuple[int, float]:
    if not isinstance(Feature, MirrorSpec):
        return Index, 0.0
    Plane = Features[Feature.PlaneIndex]
    if not isinstance(Plane, PlaneSpec) or Plane.BasePlane != "yz":
        raise ValueError("Fusion mirrors require an offset plane parallel to YZ")
    return Index, Plane.OffsetMm / 10.0


# the level round decision must stay consistent so feature parameters remain connected to the resulting geometry
def IsLevelRound(Feature: KPartFeature) -> bool:
    return (
        isinstance(Feature, (FilletSpec, ChamferSpec)) and Feature.LevelMm is not None
    )


# invalid taper input must fail here so feature parameters remain connected to the resulting geometry
def CheckTaper(Solid: PrismSolid | None, Feature: KPartFeature) -> None:
    if Solid is None or IsStateless(Feature):
        return
    if IsSealed(ReplaceValue(Solid, Rounds=())):
        raise ValueError(
            "Fusion tapered or swept bodies must come from the last solid feature"
        )
    if Solid.Rounds and not IsLevelRound(Feature):
        raise ValueError("Fusion edge rounds must follow every other solid feature")


# stage solid needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def StageSolid(
    Solid: PrismSolid | None,
    Feature: KPartFeature,
    Operation: int,
    Context: tuple[tuple[PartStage, ...], tuple[KPartFeature, ...], int],
) -> PrismSolid:
    Stages, Features, Index = Context
    CheckTaper(Solid, Feature)
    if not isinstance(Feature, (PatternSpec, CircularSpec, MirrorSpec)):
        return ApplyFeature(Solid, Feature, Operation)
    if Solid is None:
        raise ValueError("Fusion part copies require an existing body")
    if not 0 <= Feature.SourceIndex < len(Stages):
        raise ValueError("Fusion part copies must follow their source feature")
    Source = Stages[Feature.SourceIndex]
    Extra = CopyContext(Features, Feature, Index)
    return CopySolid(Solid, Feature, Operation, Source, Extra)


# the sketch stage contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def SketchStage(Feature: KPartFeature, NextTag: int, Ordinal: int) -> SketchPlan | None:
    if isinstance(Feature, ExtrudeSpec):
        return ReplaceValue(PlanSketch(Feature.Profile, NextTag), Ordinal=Ordinal)
    if isinstance(Feature, RevolveSpec):
        Profile = RevolveProfile(Feature)
        return ReplaceValue(PlanSketch(Profile, NextTag), Ordinal=Ordinal)
    if isinstance(Feature, LoftSpec):
        Lower = PlanSketch(Feature.LowerProfile, NextTag)
        return ReplaceValue(Lower, Ordinal=Ordinal)
    if isinstance(Feature, SweepSpec):
        Outline = PlanSketch(SweepProfile(Feature), NextTag)
        return ReplaceValue(Outline, Ordinal=Ordinal)
    return None


# the plan stages contract needs a stable decomposition so feature parameters remain connected to the resulting geometry
def PlanStages(
    Feature: KPartFeature, NextTag: int, Ordinal: int
) -> tuple[SketchPlan | None, SketchPlan | None, int]:
    Sketched = SketchStage(Feature, NextTag, Ordinal)
    NextTag = NextTag if Sketched is None else Sketched.NextTag
    if isinstance(Feature, SweepSpec):
        PathPlan = PlanSketch(Feature.Path, NextTag)
        return Sketched, ReplaceValue(PathPlan, Ordinal=Ordinal + 1), PathPlan.NextTag
    if not isinstance(Feature, LoftSpec):
        return Sketched, None, NextTag
    Upper = ReplaceValue(
        PlanSketch(Feature.UpperProfile, NextTag),
        Ordinal=Ordinal + 1,
        LiftCm=Feature.HeightMm / 10.0,
    )
    return Sketched, Upper, Upper.NextTag


# the count family contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def CountFamilyMut(Counts: dict[str, int], Feature: KPartFeature) -> int:
    Names = [FamilyOf(Feature).ClassName]
    if isinstance(Feature, LoftSpec):
        Names.append("DcWorkPlane")
    for NameValue in Names:
        Counts[NameValue] = Counts.get(NameValue, 0) + 1
    return Counts[Names[0]]


# sketch solid needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def SketchSolid(
    Solid: PrismSolid | None,
    Feature: KPartFeature,
    Operation: int,
    Sketched: SketchPlan,
) -> PrismSolid:
    CheckTaper(Solid, Feature)
    if isinstance(Feature, ExtrudeSpec):
        return ApplyExtrude(Solid, Feature, Operation, Sketched)
    if isinstance(Feature, RevolveSpec):
        return ApplyRevolve(Solid, Feature, Operation, Sketched)
    if isinstance(Feature, LoftSpec):
        return LoftSolid(Feature, Operation + 3)
    if isinstance(Feature, SweepSpec):
        return SweepSolid(Feature, Operation + 2)
    raise ValueError("Fusion sketched features are extrudes, revolves, lofts or sweeps")


# the new body decision must stay consistent so feature parameters remain connected to the resulting geometry
def IsNewBody(Feature: KPartFeature) -> bool:
    if isinstance(Feature, (LoftSpec, SweepSpec)):
        return True
    if not isinstance(Feature, (ExtrudeSpec, RevolveSpec)):
        return False
    return Feature.Operation == "new"


# lone body needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def LoneBody(State: KBodyState, Feature: KPartFeature) -> PrismSolid | None:
    Bodies, Shown = State
    if not Shown or IsNewBody(Feature):
        return None
    if len(Shown) != 1 and not IsStateless(Feature):
        raise ValueError("Fusion part features need exactly one visible body")
    return Bodies[Shown[0]]


# the feature solid contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def FeatureSolidMut(
    State: KBodyState,
    Feature: KPartFeature,
    Operation: int,
    Context: tuple[tuple[PartStage, ...], tuple[KPartFeature, ...], int],
    Sketched: SketchPlan | None,
) -> tuple[PrismSolid, PrismSolid]:
    if isinstance(Feature, KBodySpecs):
        return BodyStageMut(State, Feature, Operation, Context[1:])
    Solid = LoneBody(State, Feature)
    if Sketched is not None:
        After = SketchSolid(Solid, Feature, Operation, Sketched)
    else:
        After = StageSolid(Solid, Feature, Operation, Context)
    if Solid is None:
        After = ReplaceValue(After, Ordinal=len(State[0]) + 1)
        State[1].append(After.Ordinal)
    State[0][After.Ordinal] = After
    return (After if Solid is None else Solid), After


# solve part needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def SolvePart(
    SpecValue: DocumentSpec,
) -> tuple[PrismSolid | None, tuple[PartStage, ...]]:
    Policy = AuthorPolicy()
    BaseValue = BaseSolid(SpecValue, Policy)
    IsPart = BaseValue is None
    Operation = Policy.FirstOperationId + (0 if IsPart else 3)
    State: KBodyState = ({}, []) if BaseValue is None else ({1: BaseValue}, [1])
    StateId = Policy.HistoryCurrentId - (1 if IsPart else 0)
    NextTag = Policy.FirstSketchTag + (0 if IsPart else KBaseSketchTags)
    Counts: dict[str, int] = {"DcExtrudeFeature": 0 if IsPart else 1}
    Stages: list[PartStage] = []
    for Index, Feature in enumerate(SpecValue.Features):
        FamilyIndex = CountFamilyMut(Counts, Feature)
        Drawn = sum(
            (Stage.Sketch is not None) + (Stage.Upper is not None) for Stage in Stages
        )
        Sketched, Upper, NextTag = PlanStages(Feature, NextTag, Drawn + 2 - IsPart)
        Context = (tuple(Stages), SpecValue.Features, Index)
        Before, After = FeatureSolidMut(State, Feature, Operation, Context, Sketched)
        if len(State[0]) > KBodyLimit:
            raise ValueError("Fusion parts hold at most sixteen bodies")
        Count = OperationsOf(Feature)
        StateId += 0 if IsStateless(Feature) else 1
        Places = (tuple(range(Operation, Operation + Count)), StateId)
        Bodies = tuple(State[0][Ordinal] for Ordinal in sorted(State[0]))
        Stages.append(
            PartStage(
                Feature,
                Before,
                After,
                *Places,
                FamilyIndex,
                Sketched,
                Bodies,
                tuple(State[1]),
                Upper,
            )
        )
        Operation += Count
    return BaseValue, tuple(Stages)
