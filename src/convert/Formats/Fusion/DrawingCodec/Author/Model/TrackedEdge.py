from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue


# tracked edge needs an explicit state contract so sheet objects retain their intended document relationships
@MakeDataClass(frozen=True, slots=True)
class TrackedEdge:
    Recipe: RecipeValue
    FirstId: int | None = None
