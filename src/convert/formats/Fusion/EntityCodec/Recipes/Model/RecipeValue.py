from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipePayload import (
    KRecipePayload,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeTag import RecipeTag


@MakeDataClass(frozen=True, slots=True)
class RecipeValue:
    Version: int
    Tags: tuple[tuple[RecipeTag, ...], ...]
    LwdTags: tuple[tuple[RecipeTag, ...], ...]
    Payload: KRecipePayload
