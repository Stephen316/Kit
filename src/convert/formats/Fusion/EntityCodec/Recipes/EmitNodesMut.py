from convert.formats.Fusion.EntityCodec.Recipes.EmitCountMut import EmitCountMut
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipePayload import (
    KRecipePayload,
)
from convert.formats.Fusion.EntityCodec.Recipes.RecipeCalls import KRecipeWriter
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitNodesMut(
    Output: FeatureSink,
    Children: tuple[KRecipePayload, ...],
    ChildType: type[KRecipePayload],
    Catalog: EntityCatalog,
    Depth: int,
    Writer: KRecipeWriter,
) -> None:
    EmitCountMut(Output, Children, Catalog)
    for Child in Children:
        if type(Child) is not ChildType:
            raise ValueError("Fusion recipe child has the wrong payload type")
        Writer(Output, Child, Catalog, Depth + 1)
