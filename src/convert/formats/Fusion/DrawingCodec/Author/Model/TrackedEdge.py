from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue


@MakeDataClass(frozen=True, slots=True)
class TrackedEdge:
    Recipe: RecipeValue
    FirstId: int | None = None
