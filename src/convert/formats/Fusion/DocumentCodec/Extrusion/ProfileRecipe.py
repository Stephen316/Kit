from convert.formats.Fusion.DocumentCodec.Extrusion.RecipeValues import CircleLoop
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Rectangle.RectangleTag import RectangleTag


def ProfileRecipe(Author: AuthorState) -> dict[str, object]:
    FirstTag = Author.Policy.FirstSketchTag
    if Author.SpecValue.ProfileKind != "cuboid":
        return CircleLoop(FirstTag + 2)
    return {
        "first": [RectangleTag(FirstTag + Index + 5, 0) for Index in range(4)],
        "second": True,
    }
