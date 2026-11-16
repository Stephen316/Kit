from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe


# bound face recipe needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class BoundFaceRecipe:
    PrimaryTagIndex: int
    LwdTagIndex: int
    Edges: tuple[EdgeRecipe, ...]
