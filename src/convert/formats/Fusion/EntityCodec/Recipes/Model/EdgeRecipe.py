from __future__ import annotations

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe


@MakeDataClass(frozen=True, slots=True)
class EdgeRecipe:
    PrimaryTagIndex: int
    LwdTagIndex: int
    AdjacentFaces: tuple[FaceRecipe, ...]
    AdjacentVertices: tuple[VertexRecipe[EdgeRecipe], ...]
    ReferenceFaceIndex: int
