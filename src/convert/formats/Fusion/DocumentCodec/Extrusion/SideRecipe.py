from convert.formats.Fusion.DocumentCodec.Extrusion.RecipeValues import CurveRecipe
from convert.formats.Fusion.DocumentCodec.Model.ProfileSide import ProfileSide
from convert.formats.Fusion.DocumentCodec.Rectangle.RectangleTag import RectangleTag


def SideRecipe(SideValue: ProfileSide) -> dict[str, object]:
    if SideValue.PreviousTag is None and SideValue.FollowingTag is None:
        return CurveRecipe(SideValue.SketchTag, True)
    if SideValue.PreviousTag is None or SideValue.FollowingTag is None:
        raise ValueError("Rectangle curve recipes require both adjacent tags")
    return dict(
        version=0,
        sketchTags=[RectangleTag(SideValue.SketchTag, 1)],
        startAdjacentPrimaryTagIds=[SideValue.PreviousTag],
        endAdjacentPrimaryTagIds=[SideValue.FollowingTag],
    )
