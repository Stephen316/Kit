from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddBodyMut import (
    AddBodyMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddJoinSeed import (
    AddJoinSeedMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddRegionMut import (
    AddRegionMut,
    RegionTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddSeedsMut import (
    AddSeedsMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddTargetMut import (
    AddTargetMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.ExtrudeShape import (
    AddExtentParams,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.AddSketchRecs import (
    AddSketchRecs,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchPlan,
)


def StageRange(Author: AuthorState, Stage: PartStage) -> tuple[int, int]:
    Feature = Stage.Feature
    IsFirst = Stage.After.Ordinal == 1
    IsNew = isinstance(Feature, (LoftSpec, SweepSpec))
    if isinstance(Feature, (ExtrudeSpec, RevolveSpec)) and Feature.Operation == "new":
        IsNew = True
    if IsNew and IsFirst:
        return Author.Policy.HistoryInitialId, Stage.StateId
    return Stage.StateId - 1, Stage.StateId


def AddSeedTable(
    Author: AuthorState, Stage: PartStage, Prefix: str, Sketched: SketchPlan
) -> None:
    Feature = Stage.Feature
    if not isinstance(Feature, ExtrudeSpec):
        raise ValueError("Fusion part extrude authoring requires an extrude")
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Pairs = AddSeedsMut(Author, Prefix, Sketched, tuple(range(len(Sketched.Edges))))
    TwoSided = Feature.Extent in ("two", "symmetric")
    Operations = Stage.Operations[1:] if TwoSided else Stage.Operations[1:2]
    Count = len(Feature.Profile)
    if Feature.Operation == "new":
        Pairs.append(AddBodyMut(Author, Prefix, Count, Operations))
    if Feature.Operation == "join":
        Label = ReplaceValue(Stage.Before.BodyLabel, Merged=())
        Pairs.append(AddJoinSeedMut(Author, Prefix, Count, Operations, Label))
    Author.Change(Prefix + "progenitors", ProgenitorTagVec=Pairs, tagId=len(Pairs) + 3)


def AddExtrudeFeat(Author: AuthorState, Stage: PartStage, Prefix: str) -> None:
    Feature, Sketched = Stage.Feature, Stage.Sketch
    if not isinstance(Feature, ExtrudeSpec) or Sketched is None:
        raise ValueError("Fusion part extrude authoring requires a sketch plan")
    Reference = Author.Reference
    Operation = Stage.Operations[1]
    Names = (Feature.SketchName, "xy_plane")
    AddSketchRecs(Author, Prefix, Sketched, Names, Sketched.Ordinal)
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, "DcExtrudeFeature", None)
    Author.FindEntity(MainRole).NamedPairs = []
    Children: list[str] = []
    if Feature.Operation != "new":
        Children.extend(
            AddTargetMut(
                Author, Prefix, ReplaceValue(Stage.Before.BodyLabel, Merged=())
            )
        )
    AddRegionMut(Author, Prefix, RegionTags(Feature, Sketched, Operation))
    Children.extend([Prefix + "profile", Prefix + "region"])
    Children.extend(AddExtentParams(Author, Prefix, Feature))
    AddNodeMut(Author, Prefix + "tool", "DcExtrudeToolBody", MainRole)
    Author.Change(Prefix + "tool", rExtrudeFeature=Reference(MainRole))
    Author.Change(MainRole, rExtrudeToolBody=Reference(Prefix + "tool"))
    Children.append(Prefix + "tool")
    AddSeedTable(Author, Stage, Prefix, Sketched)
    Start, Finish = StageRange(Author, Stage)
    Author.Change(
        MainRole,
        childNodes=[Reference(RoleName) for RoleName in Children],
        profileDataRefs=[Reference(Prefix + "profile")],
        featureBaseName="Extrude",
        featureUserName=Feature.FeatureName,
        featureIndex=Stage.FamilyIndex,
        rProgenitorTable=Reference(Prefix + "progenitors"),
        startModelHS=Start,
        endModelHS=Finish,
    )
