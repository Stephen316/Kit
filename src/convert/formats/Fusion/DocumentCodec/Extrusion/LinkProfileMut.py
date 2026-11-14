from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Extrusion.ProfileRecipe import ProfileRecipe
from convert.formats.Fusion.DocumentCodec.Extrusion.ProfileSides import ProfileSides
from convert.formats.Fusion.DocumentCodec.Extrusion.SideRecipe import SideRecipe
from convert.formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole


def LinkProfileMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    Author.Change(
        "profile_model",
        dataRefs=[Reference("profile_region")],
        trackingType=65,
        rParentFeature=Reference("dc_extrude"),
    )
    ScopeValue = [
        Author.MakeGroup(
            "PassiveScopeValue",
            dict(
                assetId=Author.AssetId,
                scopeEntityIdentifier=str(Author.Roles[SketchRole(Author)]),
                scopeIdType=1,
                segmentId=Author.Policy.DesignSegmentId,
            ),
        )
    ]
    Author.Change(
        "profile_region",
        rRecipe=Reference("region_recipe"),
        rScope=ScopeValue,
        trackingType=65,
        rParentFeature=Reference("dc_extrude"),
    )
    RecipeData = [
        Author.MakeGroup(
            "SkRegionRecipeDataValue",
            dict(faceRecipe=[ProfileRecipe(Author)], originalFaceRecipes=[]),
        )
    ]
    Author.Change(
        "region_recipe",
        rSketchRegionRef=Reference("profile_region"),
        skRegionRecipe=[RecipeData],
    )
    for SideValue in ProfileSides(Author):
        Author.Change(SideValue.ProgenitorRole, rRecipe=Reference(SideValue.RecipeRole))
        Author.Change(SideValue.RecipeRole, profileEdgeTagData=SideRecipe(SideValue))
