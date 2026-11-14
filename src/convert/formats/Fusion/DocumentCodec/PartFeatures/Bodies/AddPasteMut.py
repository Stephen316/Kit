from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import BodyRole
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartCache import PartCache
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddBodyMut import (
    AddBodyRecs,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddTargetMut import (
    BodyRecipeOf,
    KBodyOperationType,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleRefs import (
    TopologyCache,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartStage import PartStage
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.AddCopyRefs import (
    AddSeedMut,
)

KBaseName = "Base Feature"
KPasteTracking = (5, 9)


def PairedBody(NameValue: str, RoleName: str) -> list[dict[str, object]]:
    return [{"name": NameValue, "metatype": "PassiveRefMetaType", "role": RoleName}]


def AddPasteRefMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, BodyTags: dict[int, int]
) -> list[str]:
    Reference = Author.Reference
    Source = Stage.Before
    DataRole, BodyRefRole = Prefix + "source", Prefix + "source_body"
    AddNodeMut(Author, DataRole, "ModelDataRef", Prefix + "feature")
    AddNodeMut(Author, BodyRefRole, "DRBody", Prefix + "feature")
    Recipe: dict[str, object] = {"m_Recipe": BodyRecipeOf(Source.BodyLabel)}
    Author.Allocate(BodyRefRole + "_recipe", "ASMRecipe", Fields=Recipe)
    CacheRole = BodyRefRole + "_topology"
    TopologyCache(Author, CacheRole, BodyTags[Source.Ordinal])
    SeedRef = AddSeedMut(Author, CacheRole, BodyRole(Source.Ordinal, "body"))
    Author.Change(CacheRole, progenitor=SeedRef)
    Author.Change(
        DataRole, dataRefs=[Reference(BodyRefRole)], trackingType=KPasteTracking[0]
    )
    Author.Change(
        BodyRefRole,
        rRecipe=Reference(BodyRefRole + "_recipe"),
        rScope=PartScope(Author),
        caches=[Reference(CacheRole)],
        refBodies=[Reference(BodyRole(Source.Ordinal, "dc_body"))],
        trackingType=KPasteTracking[1],
        operIdTypeMap=[
            {"key": int(Source.BodyLabel.PrimaryId), "value": KBodyOperationType}
        ],
    )
    return [DataRole, BodyRefRole]


def AddCachedMut(
    Author: AuthorState, Stage: PartStage, RoleName: str, PairName: str
) -> str:
    Reference = Author.Reference
    Author.Allocate(
        RoleName,
        "Body",
        ParentRole="cache_bodies",
        NamedPairs=PairedBody("BASEFEAT_PM_BODY_REF", PairName),
    )
    if "cache_passive_ids" not in Author.Roles:
        Author.Allocate("cache_passive_ids", "PassiveIdGenerator")
        Author.Change("cache_passive_ids", rBodies=Reference("cache_bodies"))
    Cached = [Reference(Named) for Named in Author.Roles if Named.startswith("pm_body")]
    Author.Change(
        "cache_bodies",
        creationIndex=len(Cached),
        groupChildren=Cached,
        children=list(Cached),
        passiveIdGenerator=Reference("cache_passive_ids"),
    )
    BodyUuid = str(MakeUuid())
    Author.Change(
        RoleName,
        actIdentifier=str(Author.Policy.DesignSegmentId)
        + "_"
        + str(Author.Roles[RoleName]),
        cache=PartCache(Author, Stage.After),
        creationIndex=len(Cached),
        isVisible=False,
        massProperties=Author.MakeValue("MassPropertiesValue"),
        persistentId=BodyUuid,
        rGroupParent=Reference("cache_bodies"),
        userName="",
    )
    return BodyUuid


def AddBaseMut(Author: AuthorState, Stage: PartStage, Prefix: str) -> None:
    Reference = Author.Reference
    BaseRole, DataRole = Prefix + "base", Prefix + "modeling"
    Ordinal = Stage.After.Ordinal
    CachedRole, ShownRole = BodyRole(Ordinal, "pm_body"), BodyRole(Ordinal, "body")
    AddNodeMut(Author, BaseRole, "DcBaseFeature", None)
    Author.FindEntity(BaseRole).Subjects = [CachedRole, ShownRole]
    AddNodeMut(Author, DataRole, "DcDirectModelingData", BaseRole, HasStatus=False)
    Author.Change(DataRole, rBaseFeature=Reference(BaseRole))
    CachedUuid = AddCachedMut(Author, Stage, CachedRole, ShownRole)
    ShownUuid = AddBodyRecs(Author, Ordinal, BaseRole)
    Author.FindEntity(ShownRole).NamedPairs = PairedBody(
        "BASEFEAT_DM_BODY_REF", CachedRole
    )
    SeedRole = Prefix + "base_seed"
    SeedFields: dict[str, object] = {"bodyUuid": CachedUuid, "outBodyUuid": ShownUuid}
    Author.Allocate(SeedRole, "BodyUuidProgenitor", Fields=SeedFields)
    Author.Allocate(Prefix + "base_progenitors", "ProgenitorTable")
    Author.Change(
        Prefix + "base_progenitors",
        ProgenitorTagVec=[{"first": Reference(SeedRole), "second": 1}],
        tagId=2,
    )
    SourceRole = BodyRole(Stage.Before.Ordinal, "body")
    SourceUuid = Author.FindEntity(SourceRole).FieldValues["persistentId"]
    Author.Change(
        BaseRole,
        AssoctedPIDMap=[{"key": SourceUuid, "value": CachedUuid}],
        isAssociative=True,
        sourceBodies=[Reference(CachedRole)],
        rDirectModelingData=Reference(DataRole),
        dcBodies=[Reference(BodyRole(Ordinal, "dc_body"))],
        childNodes=[Reference(DataRole)],
        featureBaseName=KBaseName,
        featureIndex=Stage.FamilyIndex,
        featureUserName="",
        rProgenitorTable=Reference(Prefix + "base_progenitors"),
        rGroupRepresentative=Reference(Prefix + "feature"),
        startModelHS=Stage.StateId - 1,
        endModelHS=Stage.StateId,
    )


def AddPasteMut(
    Author: AuthorState, Stage: PartStage, Prefix: str, BodyTags: dict[int, int]
) -> list[str]:
    if not isinstance(Stage.Feature, PasteSpec):
        raise ValueError("Fusion paste authoring requires a body paste")
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    AddNodeMut(Author, MainRole, "DcPasteBodies", None)
    Children = AddPasteRefMut(Author, Stage, Prefix, BodyTags)
    AddBaseMut(Author, Stage, Prefix)
    Author.Allocate(Prefix + "progenitors", "ProgenitorTable", Fields={"tagId": 1})
    Author.Change(
        MainRole,
        bodyRefs=[Reference(Prefix + "source")],
        rBaseFeature=Reference(Prefix + "base"),
        groupMembers=[Reference(MainRole), Reference(Prefix + "base")],
        rGroupRepresentative=Reference(MainRole),
    )
    return Children
