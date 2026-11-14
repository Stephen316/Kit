from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Extrude.AddTargetMut import (
    KBodyOperationType,
    BodyRecipeOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import (
    FocusRole,
)

KTangentClasses = ("DRPoint", "DRVector")
KNoTangent = -1.0


def TangentFree(Author: AuthorState) -> list[dict[str, object]]:
    Fields: dict[str, object] = {
        "tangentPointParam" + str(Index): KNoTangent for Index in range(3)
    }
    return [Author.MakeGroup("TangentPointDataValue", Fields)]


def TopologyCache(Author: AuthorState, RoleName: str, TagValue: int) -> None:
    Fields: dict[str, object] = {"cachedEntityId": TagValue, "scope": PartScope(Author)}
    Author.Allocate(RoleName, "ETCachedTopology", Fields=Fields)


def AddFaceRefMut(
    Author: AuthorState,
    Prefix: str,
    NameValue: str,
    Recipe: RecipeValue,
    Tracking: tuple[int, int],
) -> None:
    Reference = Author.Reference
    RoleName = Prefix + NameValue
    AddNodeMut(Author, RoleName, "BrepRef", Prefix + "feature")
    Author.Allocate(RoleName + "_recipe", "ASMRecipe", Fields={"m_Recipe": Recipe})
    TopologyCache(Author, RoleName + "_cache", Tracking[1])
    Author.Change(
        RoleName,
        rRecipe=Reference(RoleName + "_recipe"),
        rScope=PartScope(Author),
        caches=[Reference(RoleName + "_cache")],
        refBodies=[Reference(FocusRole(Author, "dc_body"))],
        trackingType=Tracking[0],
    )


def AddPlaceMut(
    Author: AuthorState,
    Prefix: str,
    Names: tuple[str, str],
    Fields: dict[str, object],
) -> None:
    Reference = Author.Reference
    RoleName, ClassName = Names
    if ClassName in KTangentClasses:
        Fields = dict(Fields, tangentPointData=TangentFree(Author))
    AddNodeMut(Author, Prefix + RoleName, ClassName, Prefix + "feature")
    Author.Allocate(Prefix + RoleName + "_cache", "ETCachedMatrix3d")
    Author.Change(
        Prefix + RoleName,
        caches=[Reference(Prefix + RoleName + "_cache")],
        trackingType=4,
        **Fields,
    )


def AddThroughMut(
    Author: AuthorState, Prefix: str, Label: FaceLabel, BodyTag: int
) -> list[str]:
    Reference = Author.Reference
    Owner = Prefix + "feature"
    AddNodeMut(Author, Prefix + "extent", "ModelDataRef", Owner)
    AddNodeMut(Author, Prefix + "extent_body", "DRBody", Owner)
    Author.Allocate(Prefix + "extent_cache", "ETCachedMatrix3d")
    Recipe: dict[str, object] = {"m_Recipe": BodyRecipeOf(Label)}
    Author.Allocate(Prefix + "extent_recipe", "ASMRecipe", Fields=Recipe)
    Entity: dict[str, object] = {"m_entityId": Author.Roles[FocusRole(Author, "body")]}
    Author.Allocate(Prefix + "extent_entity", "EntityRecipe", Fields=Entity)
    SeedValue: dict[str, object] = {
        "m_entityRecipe": Reference(Prefix + "extent_entity")
    }
    Author.Allocate(Prefix + "extent_seed", "EntityProgenitor", Fields=SeedValue)
    TopologyCache(Author, Prefix + "extent_topology", BodyTag)
    Author.Change(
        Prefix + "extent_topology", progenitor=Reference(Prefix + "extent_seed")
    )
    Author.Change(
        Prefix + "extent",
        dataRefs=[Reference(Prefix + "extent_body")],
        caches=[Reference(Prefix + "extent_cache")],
        trackingType=5,
    )
    Author.Change(
        Prefix + "extent_body",
        rRecipe=Reference(Prefix + "extent_recipe"),
        rScope=PartScope(Author),
        caches=[Reference(Prefix + "extent_topology")],
        refBodies=[Reference(FocusRole(Author, "dc_body"))],
        trackingType=9,
        operIdTypeMap=[{"key": int(Label.PrimaryId), "value": KBodyOperationType}],
    )
    return [Prefix + "extent", Prefix + "extent_body"]
