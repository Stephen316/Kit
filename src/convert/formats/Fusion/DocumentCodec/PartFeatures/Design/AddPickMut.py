from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import (
    FocusRole,
)


def AddPickMut(
    Author: AuthorState,
    Prefix: str,
    Recipe: RecipeValue,
    TrackingType: int,
    CacheClass: str,
    CacheFields: dict[str, object],
) -> None:
    Owner = Prefix + "feature"
    AddNodeMut(Author, Prefix + "target", "ModelDataRef", Owner)
    AddNodeMut(Author, Prefix + "pick", "BrepRef", Owner)
    Author.Allocate(Prefix + "target_cache", "ETCachedMatrix3d")
    Author.Allocate(Prefix + "pick_recipe", "ASMRecipe", Fields={"m_Recipe": Recipe})
    Author.Allocate(Prefix + "pick_cache", CacheClass, Fields=CacheFields)
    Reference = Author.Reference
    Author.Change(
        Prefix + "target",
        dataRefs=[Reference(Prefix + "pick")],
        caches=[Reference(Prefix + "target_cache")],
        trackingType=TrackingType,
    )
    Author.Change(
        Prefix + "pick",
        rRecipe=Reference(Prefix + "pick_recipe"),
        rScope=PartScope(Author),
        caches=[Reference(Prefix + "pick_cache")],
        refBodies=[Reference(FocusRole(Author, "dc_body"))],
        trackingType=TrackingType,
    )


def AddBrepRefMut(
    Author: AuthorState,
    Roles: tuple[str, str],
    Recipe: RecipeValue,
    Cache: tuple[str, dict[str, object], int],
) -> str:
    OwnerRole, RoleName = Roles
    CacheClass, CacheFields, Tracking = Cache
    AddNodeMut(Author, RoleName, "BrepRef", OwnerRole)
    Author.Allocate(RoleName + "_recipe", "ASMRecipe", Fields={"m_Recipe": Recipe})
    Author.Allocate(RoleName + "_cache", CacheClass, Fields=CacheFields)
    Reference = Author.Reference
    Author.Change(
        RoleName,
        rRecipe=Reference(RoleName + "_recipe"),
        rScope=PartScope(Author),
        caches=[Reference(RoleName + "_cache")],
        refBodies=[Reference(FocusRole(Author, "dc_body"))],
        trackingType=Tracking,
    )
    return RoleName


def AddMorePickMut(
    Author: AuthorState,
    Prefix: str,
    RoleName: str,
    Recipe: RecipeValue,
    CacheFields: dict[str, object],
) -> None:
    Roles = (Prefix + "feature", RoleName)
    _ = AddBrepRefMut(Author, Roles, Recipe, ("ETCachedLineSeg3d", CacheFields, 8))
