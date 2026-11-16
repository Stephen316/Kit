from convert.Formats.Fusion.EntityCodec.Recipes.EmitCountMut import EmitCountMut
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipePayload import (
    KRecipePayload,
)
from convert.Formats.Fusion.EntityCodec.Recipes.RecipeCalls import KRecipeWriter
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


# the nodes operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
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
