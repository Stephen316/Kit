from convert.formats.Fusion.DocumentCodec.Materials.LinkMaterialMut import (
    LinkMaterialMut,
)
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Construct.AddWorkMut import (
    AddWorkMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddCornerMut import (
    AddCornerMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddShellMut import (
    AddShellMut,
    ShellTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.LinkCornerMut import (
    LinkCornerMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.LinkFeatureMut import (
    LinkFeatureMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.LinkTimeline import (
    LinkTimeline,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartCache import PartCache
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.RoofTag import (
    CapTagSet,
    RoofTagSet,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddExtrudeFeat import (
    AddExtrudeFeat,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleMut import (
    AddHoleMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.HoleRoot import RoofMiddle
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Sweep.AddSweepFeat import (
    AddSweepFeat,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Loft.AddLoftFeat import (
    AddLoftFeat,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddCopyMut import (
    AddCopyMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddPlaneMut import (
    AddPlaneMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Move.AddMoveMut import AddMoveMut
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Draft.AddDraftMut import (
    AddDraftMut,
    DraftTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Offset.AddOffsetMut import (
    AddOffsetMut,
    OffsetPick,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Revolve.AddRevolveFeat import (
    AddRevolveFeat,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.AddBodyFeat import (
    AddBodyStage,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.BodyStage import (
    KBodySpecs,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.LinkBodiesMut import (
    LinkBodiesMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.TagState import (
    BodyTags,
    TagState,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FamilyRules import (
    IsStateless,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart


def AddStageMut(
    Author: AuthorState,
    Stage: PartStage,
    Prefix: str,
    Context: tuple[tuple[TagState, ...], int, tuple[PartStage, ...]],
) -> list[str]:
    Solids, Place, Stages = Context
    Feature = Stage.Feature
    if isinstance(Feature, ShellSpec):
        return AddShellMut(Author, Stage, Prefix, ShellTags(Solids, Place, Stage))
    if isinstance(Feature, HoleSpec):
        Middle = RoofMiddle(Stages, Stage)
        return AddHoleMut(
            Author, Stage, Prefix, (RoofTagSet(Solids, Place + 1), Middle)
        )
    if isinstance(Feature, PlaneSpec):
        return AddPlaneMut(Author, Stage, Prefix)
    if isinstance(Feature, (AxisSpec, PointSpec)):
        return AddWorkMut(Author, Stage, Prefix)
    if isinstance(Feature, MoveSpec):
        return AddMoveMut(Author, Stage, Prefix)
    if isinstance(Feature, OffsetSpec):
        return AddOffsetMut(Author, Stage, Prefix, OffsetPick(Solids, Place, Stage))
    if isinstance(Feature, DraftSpec):
        return AddDraftMut(Author, Stage, Prefix, DraftTags(Solids, Place, Stage))
    if isinstance(Feature, (PatternSpec, CircularSpec, MirrorSpec)):
        Source = Stages[Feature.SourceIndex].Feature
        IsRoof = isinstance(Feature, PatternSpec) or isinstance(Source, HoleSpec)
        TagSet = CapTagSet(Solids, Place + 1, IsRoof)
        return AddCopyMut(Author, Stage, Prefix, TagSet)
    Children = AddCornerMut(Author, Stage, Prefix)
    LinkCornerMut(Author, Stage, Prefix)
    return Children


def AddSketchedMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, Stages: tuple[PartStage, ...]
) -> None:
    if isinstance(Stage.Feature, LoftSpec):
        AddLoftFeat(Author, Stage, Prefix, Stages)
        return
    if isinstance(Stage.Feature, SweepSpec):
        AddSweepFeat(Author, Stage, Prefix)
        return
    Builder = AddExtrudeFeat
    if isinstance(Stage.Feature, RevolveSpec):
        Builder = AddRevolveFeat
    Builder(Author, Stage, Prefix)


def AddPartMut(Author: AuthorState) -> None:
    BaseValue, Stages = SolvePart(Author.SpecValue)
    States = (
        () if BaseValue is None else (TagState(BaseValue, (BaseValue,)),)
    ) + tuple(TagState(Stage.After, Stage.Bodies) for Stage in Stages)
    Journal = (() if BaseValue is None else ((BaseValue,),)) + tuple(
        Stage.Bodies for Stage in Stages if not IsStateless(Stage.Feature)
    )
    JournalTags = BodyTags(Journal)
    Offset = 0 if BaseValue is not None else -1
    for Index, Stage in enumerate(Stages):
        Prefix = "f" + str(Index + 1) + "_"
        Author.FocusOrdinal = Stage.Before.Ordinal
        if isinstance(Stage.Feature, (ExtrudeSpec, RevolveSpec, LoftSpec, SweepSpec)):
            AddSketchedMut(Author, Stage, Prefix, Stages)
            continue
        if isinstance(Stage.Feature, KBodySpecs):
            Children = AddBodyStage(Author, Stage, Prefix, JournalTags)
        else:
            Context = (States, Index + Offset, Stages)
            Children = AddStageMut(Author, Stage, Prefix, Context)
        LinkFeatureMut(Author, Stage, Prefix, Children)
    Author.FocusOrdinal = 1
    LinkTimeline(Author, Stages)
    if BaseValue is None:
        LinkMaterialMut(Author)
        LinkBodiesMut(Author, Stages[-1], JournalTags)
        return
    Author.Change("body", cache=PartCache(Author, States[-1].Focus))
