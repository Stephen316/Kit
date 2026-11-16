from __future__ import annotations

from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe


# edge recipe needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class EdgeRecipe:
    PrimaryTagIndex: int
    LwdTagIndex: int
    AdjacentFaces: tuple[FaceRecipe, ...]
    AdjacentVertices: tuple[VertexRecipe[EdgeRecipe], ...]
    ReferenceFaceIndex: int
