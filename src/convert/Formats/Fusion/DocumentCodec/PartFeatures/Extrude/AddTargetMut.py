from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.Formats.Fusion.EntityCodec.Recipes.Model.BodyRecipe import BodyRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeTag import RecipeTag
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import (
    FocusRole,
)

# body operation type must remain consistent across callers so feature parameters remain connected to the resulting geometry
KBodyOperationType = 33


# the body recipe of contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def BodyRecipeOf(Label: FaceLabel) -> RecipeValue:
    TagValue = RecipeTag(
        tuple(Label.PrimaryId.encode("ascii")), Label.SecondaryId, Label.OperationIds, 0
    )
    return RecipeValue(3, ((TagValue,),), (), BodyRecipe(0, -1))


# the target operation needs a consistent construction rule so feature parameters remain connected to the resulting geometry
def AddTargetMut(Author: AuthorState, Prefix: str, Label: FaceLabel) -> list[str]:
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    AddNodeMut(Author, Prefix + "target", "ModelDataRef", MainRole)
    AddNodeMut(Author, Prefix + "target_body", "DRBody", MainRole)
    Author.Allocate(Prefix + "target_cache", "ETCachedMatrix3d")
    Author.Allocate(
        Prefix + "target_recipe", "ASMRecipe", Fields={"m_Recipe": BodyRecipeOf(Label)}
    )
    Author.Change(
        Prefix + "target",
        dataRefs=[Reference(Prefix + "target_body")],
        caches=[Reference(Prefix + "target_cache")],
        trackingType=8,
    )
    Author.Change(
        Prefix + "target_body",
        rRecipe=Reference(Prefix + "target_recipe"),
        rScope=PartScope(Author),
        refBodies=[Reference(FocusRole(Author, "dc_body"))],
        trackingType=8,
        operIdTypeMap=[{"key": int(Label.PrimaryId), "value": KBodyOperationType}],
    )
    Author.Change(MainRole, targetDataRefs=[Reference(Prefix + "target")])
    return [Prefix + "target", Prefix + "target_body"]
