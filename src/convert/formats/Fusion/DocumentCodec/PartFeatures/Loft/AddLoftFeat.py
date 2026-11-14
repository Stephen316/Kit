from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.LinkFeatureMut import (
    LinkFeatureMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddBodyMut import (
    AddBodyMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddExtrudeFeat import (
    StageRange,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddRegionMut import (
    AddRegionMut,
    RegionTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.ExtrudeShape import (
    KBooleanCodes,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddPlaneMut import (
    AddPlaneMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.AddSketchRecs import (
    AddSketchRecs,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchPlan,
)
from convert.formats.Fusion.DocumentCodec.Rectangle.RectangleTag import RectangleTag

KNoRail = -1
KProfileSection = 2
KLoftModes: dict[str, object] = dict(
    IsEndTangencyFlippedDirection=True,
    IsStartTangencyFlippedDirection=True,
    bChainOption=True,
    bMergeCurves=True,
    booleanOperation=KBooleanCodes["new"],
    endRailsTakeOffIndex=KNoRail,
    isSolidOperation=True,
    startRailsTakeOffIndex=KNoRail,
)


def LoftPlans(Stage: PartStage) -> tuple[LoftSpec, SketchPlan, SketchPlan]:
    Feature, Lower, Upper = Stage.Feature, Stage.Sketch, Stage.Upper
    if not isinstance(Feature, LoftSpec) or Lower is None or Upper is None:
        raise ValueError("Fusion loft authoring requires both section sketches")
    return Feature, Lower, Upper


def AddLoftPlaneMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, Stages: tuple[PartStage, ...]
) -> None:
    Feature = LoftPlans(Stage)[0]
    Place = Stages.index(Stage)
    Count = sum(
        isinstance(Other.Feature, (PlaneSpec, LoftSpec))
        for Other in Stages[: Place + 1]
    )
    Plane = PlaneSpec(Feature.HeightMm, "xy", Feature.PlaneName)
    Operations = Stage.Operations[1:2]
    PlaneStage = PartStage(Plane, Stage.Before, Stage.After, Operations, -1, Count)
    Children = AddPlaneMut(Author, PlaneStage, Prefix + "wp_")
    LinkFeatureMut(Author, PlaneStage, Prefix + "wp_", Children)


def AddCurveSeedMut(Author: AuthorState, RoleName: str, CurveTag: int) -> object:
    Author.Allocate(RoleName, "SketchCurveProgenitor", NamedPairs=[])
    Author.Allocate(RoleName + "_recipe", "SketchCurveRecipe")
    Author.Change(RoleName, rRecipe=Author.Reference(RoleName + "_recipe"))
    Author.Change(
        RoleName + "_recipe",
        profileEdgeTagData=dict(
            version=0,
            sketchTags=[RectangleTag(CurveTag, 1)],
            startAdjacentPrimaryTagIds=[],
            endAdjacentPrimaryTagIds=[],
        ),
    )
    return Author.Reference(RoleName)


def AddLoftTable(Author: AuthorState, Stage: PartStage, Prefix: str) -> None:
    _, Lower, Upper = LoftPlans(Stage)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Pairs: list[dict[str, object]] = []
    for Index, Edges in enumerate(zip(Lower.Edges, Upper.Edges, strict=True)):
        SeedRole = Prefix + "loft_seed" + str(Index)
        Sections = [
            AddCurveSeedMut(Author, SeedRole + SideName, EdgeValue.CurveTag)
            for SideName, EdgeValue in zip(("_lower", "_upper"), Edges)
        ]
        Author.Allocate(
            SeedRole, "LoftProgenitor", Fields={"sectionProgenitors": Sections}
        )
        Pairs.append({"first": Author.Reference(SeedRole), "second": Index + 3})
    Count = len(Lower.Edges) + 2
    Pairs.append(AddBodyMut(Author, Prefix, Count, Stage.Operations[3:], 1))
    Author.Change(Prefix + "progenitors", ProgenitorTagVec=Pairs, tagId=len(Pairs) + 3)


def AddSectionsMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> list[str]:
    Feature, Lower, Upper = LoftPlans(Stage)
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    Sides = (
        (Prefix, Feature.LowerProfile, Lower),
        (Prefix + "up_", Feature.UpperProfile, Upper),
    )
    Children: list[str] = []
    for StemName, Profile, Sketched in Sides:
        Shaper = ExtrudeSpec(Profile, Feature.HeightMm)
        TagList = RegionTags(Shaper, Sketched, Stage.Operations[3])
        AddRegionMut(Author, StemName, TagList, MainRole)
        Author.Allocate(StemName + "section", "DcLoftSectionData")
        Author.Change(
            StemName + "section",
            rParentFeature=Reference(MainRole),
            rSectionRef=Reference(StemName + "profile"),
            sectionType=KProfileSection,
        )
        Children.extend([StemName + "profile", StemName + "region"])
    Sections = [Reference(StemName + "section") for StemName, _, _ in Sides]
    Author.Change(MainRole, sectionDatas=Sections)
    return Children


def AddLoftFeat(
    Author: AuthorState, Stage: PartStage, Prefix: str, Stages: tuple[PartStage, ...]
) -> None:
    Feature, Lower, Upper = LoftPlans(Stage)
    Reference = Author.Reference
    AddSketchRecs(Author, Prefix, Lower, (Feature.LowerName, "xy_plane"), Lower.Ordinal)
    AddLoftPlaneMut(Author, Stage, Prefix, Stages)
    UpperNames = (Feature.UpperName, Prefix + "wp_plane")
    AddSketchRecs(Author, Prefix + "up_", Upper, UpperNames, Upper.Ordinal)
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, "DcLoftFeature", None)
    Author.FindEntity(MainRole).NamedPairs = []
    Children = AddSectionsMut(Author, Stage, Prefix)
    AddNodeMut(Author, Prefix + "tool", "DcLoftToolBody", MainRole)
    Author.Change(Prefix + "tool", rLoftFeature=Reference(MainRole))
    Author.Change(MainRole, rLoftToolBody=Reference(Prefix + "tool"))
    AddLoftTable(Author, Stage, Prefix)
    Start, Finish = StageRange(Author, Stage)
    Author.Change(
        MainRole,
        childNodes=[Reference(RoleName) for RoleName in Children + [Prefix + "tool"]],
        featureBaseName="Loft",
        featureUserName=Feature.FeatureName,
        **KLoftModes,
        featureIndex=Stage.FamilyIndex,
        rProgenitorTable=Reference(Prefix + "progenitors"),
        startModelHS=Start,
        endModelHS=Finish,
    )
