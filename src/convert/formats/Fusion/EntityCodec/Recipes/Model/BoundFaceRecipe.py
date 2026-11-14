from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe


@MakeDataClass(frozen=True, slots=True)
class BoundFaceRecipe:
    PrimaryTagIndex: int
    LwdTagIndex: int
    Edges: tuple[EdgeRecipe, ...]
