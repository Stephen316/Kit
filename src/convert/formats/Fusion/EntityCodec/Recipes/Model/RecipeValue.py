from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipePayload import (
    KRecipePayload,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeTag import RecipeTag


# recipe value needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class RecipeValue:
    Version: int
    Tags: tuple[tuple[RecipeTag, ...], ...]
    LwdTags: tuple[tuple[RecipeTag, ...], ...]
    Payload: KRecipePayload
