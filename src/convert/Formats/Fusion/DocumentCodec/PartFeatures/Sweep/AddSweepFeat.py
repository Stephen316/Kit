from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddBodyMut import (
    AddBodyMut,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddExtrudeFeat import (
    StageRange,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddRegionMut import (
    AddRegionMut,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Extrude.ExtrudeShape import (
    KBooleanCodes,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Loft.AddLoftFeat import (
    AddCurveSeedMut,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Profile.AddSketchRecs import (
    AddSketchRecs,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchFrame import (
    FrameNormal,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchPlan,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Revolve.AddRevolveFeat import (
    SketchTags,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Sweep.AddPathRefs import (
    KPathSketch,
    AddEdgeSeedMut,
    AddPathMut,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Sweep.SweepTags import (
    FaceIds,
    SweepTags,
)

# profile plane must remain consistent across callers so feature parameters remain connected to the resulting geometry
KProfilePlane = "xz_plane"

# the sweep modes vocabulary must stay centralized so parametric feature reconstruction agrees on supported native identities
KSweepModes: dict[str, object] = dict(
    chainPropagation=True,
    isAlongDirectionSameAsProfileNormal=3,
    isSolidOperation=True,
    isXScale=True,
    isYScale=True,
    sweepType=2,
)

# the tool modes vocabulary must stay centralized so parametric feature reconstruction agrees on supported native identities
KToolModes: dict[str, object] = dict(isAlongDistanceParameterValid=True)

# the sweep parameters order must stay explicit so feature parameters remain connected to the resulting geometry
KSweepParams = (
    ("along", "AlongDistance", 1.0, "", "rAlongDistance"),
    ("against", "AgainstDistance", 0.0, "", "rAgainstDistance"),
    ("rail_along", "AlongRailDistance", 1.0, "", "rAlongRailDistance"),
    ("rail_against", "AgainstRailDistance", 1.0, "", "rAgainstRailDistance"),
    ("twist", "TwistAngle", 0.0, "deg", "rTwistAngle"),
    ("taper", "TaperAngle", 0.0, "deg", "rTaperAngle"),
)


# sweep plans needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def SweepPlans(Stage: PartStage) -> tuple[SweepSpec, SketchPlan, SketchPlan]:
    Feature, Profile, PathPlan = Stage.Feature, Stage.Sketch, Stage.Upper
    if not isinstance(Feature, SweepSpec) or Profile is None or PathPlan is None:
        raise ValueError("Fusion sweep authoring requires profile and path sketches")
    return Feature, Profile, PathPlan


# the sweep parameters operation needs a consistent construction rule so feature parameters remain connected to the resulting geometry
def AddSweepParams(Author: AuthorState, Prefix: str) -> list[str]:
    Owner = Prefix + "feature"
    for StemName, NameValue, Amount, UnitName, FieldName in KSweepParams:
        Expression = "0.0 deg" if UnitName else None
        AddParamMut(
            Author, Prefix + StemName, Owner, NameValue, Amount, UnitName, Expression
        )
        Author.Change(Owner, **{FieldName: Author.Reference(Prefix + StemName)})
    return [Prefix + RowValue[0] for RowValue in KSweepParams]


# the sweep table operation needs a consistent construction rule so feature parameters remain connected to the resulting geometry
def AddSweepTable(
    Author: AuthorState, Stage: PartStage, Prefix: str, Drawn: KPathSketch
) -> None:
    _, Profile, PathPlan = SweepPlans(Stage)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Pairs: list[dict[str, object]] = []
    for Index, Segment in enumerate(PathPlan.Edges):
        SeedName = Prefix + "path_seed" + str(Index)
        SeedRef = AddEdgeSeedMut(Author, SeedName, Segment, Drawn)
        Pairs.append({"first": SeedRef, "second": Index + 3})
    TagMap = SweepTags(len(PathPlan.Edges))
    for (SideIndex, Place), TagValue in TagMap.items():
        RoleName = Prefix + "sweep_seed" + str(TagValue)
        Fields = dict(
            profileProg=AddCurveSeedMut(
                Author, RoleName + "_profile", Profile.Edges[SideIndex].CurveTag
            ),
            pathProg=AddCurveSeedMut(Author, RoleName + "_path", Place + 3),
        )
        Author.Allocate(RoleName, "SweepFaceProgenitor", Fields=Fields, NamedPairs=[])
        Pairs.append({"first": Author.Reference(RoleName), "second": TagValue})
    Operations, Labels = Stage.Operations[2:], FaceIds(TagMap)
    Pairs.append(AddBodyMut(Author, Prefix, len(Pairs), Operations, 3, Labels))
    Author.Change(Prefix + "progenitors", ProgenitorTagVec=Pairs, tagId=len(Pairs) + 3)


# the sweep feat operation needs a consistent construction rule so feature parameters remain connected to the resulting geometry
def AddSweepFeat(Author: AuthorState, Stage: PartStage, Prefix: str) -> None:
    Feature, Profile, PathPlan = SweepPlans(Stage)
    Reference, MainRole = Author.Reference, Prefix + "feature"
    Names = (Feature.ProfileName, KProfilePlane)
    AddSketchRecs(Author, Prefix, Profile, Names, Profile.Ordinal)
    Names = (Feature.PathName, "xy_plane")
    AddSketchRecs(Author, Prefix + "up_", PathPlan, Names, PathPlan.Ordinal)
    AddNodeMut(Author, MainRole, "DcSweepFeature", None)
    Author.FindEntity(MainRole).NamedPairs = []
    AddRegionMut(Author, Prefix, SketchTags(Profile))
    Drawn = (PathPlan, Author.Roles[Prefix + "up_sketch"])
    Children = [
        Prefix + "profile",
        Prefix + "region",
        *AddPathMut(Author, Prefix, Drawn),
    ]
    Children.extend(AddSweepParams(Author, Prefix))
    AddNodeMut(Author, Prefix + "tool", "DcSweepToolBody", MainRole)
    Author.Change(Prefix + "tool", rSweepFeature=Reference(MainRole), **KToolModes)
    Children.append(Prefix + "tool")
    AddSweepTable(Author, Stage, Prefix, Drawn)
    Start, Finish = StageRange(Author, Stage)
    Author.Change(
        MainRole,
        booleanOperation=KBooleanCodes["new"],
        profileNormal=FrameNormal(KProfilePlane),
        **KSweepModes,
        profileDataRefs=[Reference(Prefix + "profile")],
        rSweepPathsRef=Reference(Prefix + "path"),
        rSweepToolBody=Reference(Prefix + "tool"),
        childNodes=[Reference(RoleName) for RoleName in Children],
        featureBaseName="Sweep",
        featureUserName=Feature.FeatureName,
        featureIndex=Stage.FamilyIndex,
        rProgenitorTable=Reference(Prefix + "progenitors"),
        startModelHS=Start,
        endModelHS=Finish,
    )
