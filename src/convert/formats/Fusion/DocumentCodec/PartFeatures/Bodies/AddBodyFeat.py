from dataclasses import replace as ReplaceValue
from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.AddPasteMut import (
    AddPasteMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.BodyRefs import (
    AddBodyRefMut,
    AddBodySeedMut,
    AddOccurMut,
    MarkOperation,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Bodies.CopyBodies import (
    CopyLayout,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import BodyRole
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddBodyMut import (
    AddBodyRecs,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleRefs import (
    TopologyCache,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyRingSpec import (
    BodyRingSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SplitSpec import SplitSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddCopyMut import (
    AddCountMut,
    AddGridMut,
    AddTurnMut,
    LinkBaseMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddCopyRefs import (
    AddEntityRefMut,
    AddSeedMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)

KCombineCodes = {"join": 0, "cut": 1, "intersect": 2}


def StageBody(Stage: PartStage, Ordinal: int) -> PrismSolid:
    return next(Solid for Solid in Stage.Bodies if Solid.Ordinal == Ordinal)


def AddToolMut(
    Author: AuthorState, Prefix: str, Index: int, Context: tuple[PrismSolid, int, int]
) -> list[str]:
    ToolSolid, Operation, TagValue = Context
    NameValue = "tool" + str(Index + 1)
    Roles = AddBodyRefMut(Author, Prefix, NameValue, ToolSolid, (5, 9))
    MarkOperation(Author, Roles[0], Operation)
    CacheRole = Roles[1] + "_topology"
    TopologyCache(Author, CacheRole, TagValue)
    SeedRef = AddSeedMut(Author, CacheRole, BodyRole(ToolSolid.Ordinal, "body"))
    Author.Change(CacheRole, progenitor=SeedRef)
    Author.Change(Roles[1], caches=[Author.Reference(CacheRole)], updateFlag=2)
    return Roles


def AddCombineMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, BodyTags: dict[int, int]
) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, CombineSpec):
        raise ValueError("Fusion combine authoring requires a combine feature")
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    Operation = Stage.Operations[0]
    AddNodeMut(Author, MainRole, "DcCombineFeature", None)
    Children: list[str] = []
    for Index, Ordinal in enumerate(Feature.ToolBodies):
        Context = (StageBody(Stage, Ordinal), Operation, BodyTags[Ordinal])
        Children += AddToolMut(Author, Prefix, Index, Context)
    Children += AddBodyRefMut(Author, Prefix, "target", Stage.Before, (4, 8))
    Removed = [] if Feature.KeepTools else list(Feature.ToolBodies)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable", Fields={"tagId": 1})
    Author.Change(
        MainRole,
        booleanOperation=KCombineCodes[Feature.Operation],
        isKeepTools=Feature.KeepTools,
        occDR2FeatIdMap=AddOccurMut(Author, Prefix, Operation),
        toolBodiesDateRefs=[
            Reference(Prefix + "tool" + str(Index + 1))
            for Index in range(len(Feature.ToolBodies))
        ],
        removedBodies=[Reference(BodyRole(Ordinal, "dc_body")) for Ordinal in Removed],
    )
    return Children


def AddSplitMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, SplitSpec):
        raise ValueError("Fusion split authoring requires a split feature")
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    Operation = Stage.Operations[0]
    PlaneRole = "f" + str(Feature.PlaneIndex + 1) + "_plane"
    AddNodeMut(Author, MainRole, "DcSplitBodyFeature", None)
    AddNodeMut(Author, Prefix + "tool", "ModelDataRef", MainRole)
    MarkOperation(Author, Prefix + "tool", Operation)
    Author.Allocate(Prefix + "tool_cache", "ETCachedMatrix3d")
    RefRole = AddEntityRefMut(Author, Prefix, "tool_plane", (PlaneRole, 33))
    Cache: dict[str, object] = {
        "rCachedGeometry": Author.FindEntity(PlaneRole).FieldValues["plane"],
        "progenitor": AddSeedMut(Author, RefRole, PlaneRole),
    }
    Author.Allocate(RefRole + "_cache", "ETCachedPlane", Fields=Cache)
    Author.Change(RefRole, caches=[Reference(RefRole + "_cache")])
    Author.Change(
        Prefix + "tool",
        dataRefs=[Reference(RefRole)],
        caches=[Reference(Prefix + "tool_cache")],
        trackingType=33,
    )
    Children = [Prefix + "tool", RefRole]
    Children += AddBodyRefMut(Author, Prefix, "target", Stage.Before, (4, 8))
    Created = Stage.Bodies[-1]
    NewUuid = AddBodyRecs(Author, Created.Ordinal, MainRole)
    PlaneSeed = AddSeedMut(Author, Prefix + "plane_seed", PlaneRole)
    KeptSeed = AddBodySeedMut(
        Author, Prefix + "kept_seed", Stage.After, (str(MakeUuid()), Operation, True)
    )
    MadeSeed = AddBodySeedMut(
        Author, Prefix + "made_seed", Created, (NewUuid, Operation, False)
    )
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Author.Change(
        Prefix + "progenitors",
        ProgenitorTagVec=[
            {"first": PlaneSeed, "second": 1},
            {"first": KeptSeed, "second": 2},
            {"first": MadeSeed, "second": 3},
        ],
        tagId=4,
    )
    Author.Change(
        MainRole,
        isExtendTool=True,
        occDR2FeatIdMap=AddOccurMut(Author, Prefix, Operation),
        toolBodiesDR=[Reference(Prefix + "tool")],
        dcBodies=[Reference(BodyRole(Created.Ordinal, "dc_body"))],
    )
    return Children


def AddSourceMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, BodyTags: dict[int, int]
) -> list[str]:
    Reference = Author.Reference
    AddNodeMut(Author, Prefix + "source_set", "DcPatternSource", Prefix + "feature")
    Children = [Prefix + "source_set"]
    Children += AddBodyRefMut(Author, Prefix, "source", Stage.Before, (8, 8))
    CacheRole = Prefix + "source_topology"
    TopologyCache(Author, CacheRole, BodyTags[Stage.Before.Ordinal])
    SeedRef = AddSeedMut(Author, CacheRole, BodyRole(Stage.Before.Ordinal, "dc_body"))
    Author.Change(CacheRole, progenitor=SeedRef)
    Author.Change(
        Prefix + "source_set",
        caches=[
            {
                "first": Reference(Prefix + "source_body"),
                "second": [Reference(CacheRole)],
            }
        ],
        patternFeature=Reference(Prefix + "feature"),
    )
    return Children


def AddCopiesMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> None:
    MainRole = Prefix + "feature"
    Copies = Stage.Bodies[1 - len(Stage.Operations) :]
    Seeds: list[dict[str, object]] = []
    for Index, Solid in enumerate(Copies):
        BodyUuid = AddBodyRecs(Author, Solid.Ordinal, MainRole)
        SeedRole = Prefix + "copy_seed" + str(Index + 1)
        SeedRef = AddBodySeedMut(Author, SeedRole, Solid, (BodyUuid, 0, False))
        Seeds.append({"first": SeedRef, "second": Index + 1})
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable")
    Author.Change(Prefix + "progenitors", ProgenitorTagVec=Seeds, tagId=len(Seeds) + 1)
    Author.Change(
        MainRole,
        dcBodies=[
            Author.Reference(BodyRole(Solid.Ordinal, "dc_body")) for Solid in Copies
        ],
    )


def AddBodyCopyMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, BodyTags: dict[int, int]
) -> list[str]:
    Feature = Stage.Feature
    if not isinstance(Feature, (BodyGridSpec, BodyRingSpec)):
        raise ValueError("Fusion body pattern authoring requires a body pattern")
    Layout = CopyLayout(Feature)
    IsRing = isinstance(Layout, CircularSpec)
    ClassName = "DcCircularPattern" if IsRing else "DcRectangularPattern"
    AddNodeMut(Author, Prefix + "feature", ClassName, None)
    Author.Allocate(Prefix + "data", ClassName + "Data")
    Children = AddSourceMut(Author, Stage, Prefix, BodyTags)
    Count = Layout.Count if isinstance(Layout, CircularSpec) else Layout.CountU
    Children.append(AddCountMut(Author, Prefix, "countU", Count))
    if isinstance(Layout, CircularSpec):
        Children += AddTurnMut(Author, Prefix, Layout)
    else:
        Children += AddGridMut(Author, Prefix, Layout)
    LinkBaseMut(Author, Prefix, ReplaceValue(Stage, Feature=Layout))
    Author.Change(Prefix + "data", additionalAffectedBodies=[], computeType=2)
    AddCopiesMut(Author, Stage, Prefix)
    return Children


def AddBodyStage(
    Author: AuthorState, Stage: PartStage, Prefix: str, BodyTags: dict[int, int]
) -> list[str]:
    if isinstance(Stage.Feature, CombineSpec):
        return AddCombineMut(Author, Stage, Prefix, BodyTags)
    if isinstance(Stage.Feature, SplitSpec):
        return AddSplitMut(Author, Stage, Prefix)
    if isinstance(Stage.Feature, PasteSpec):
        return AddPasteMut(Author, Stage, Prefix, BodyTags)
    return AddBodyCopyMut(Author, Stage, Prefix, BodyTags)
